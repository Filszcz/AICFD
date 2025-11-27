import os
import glob
import datetime
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import wandb
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# PyG Imports
from torch_geometric.data import Data, Dataset
from torch_geometric.loader import DataLoader
from torch_geometric.nn import GATv2Conv, fps, radius_graph, knn_graph
from torch_geometric.utils import to_dense_batch
from torch_scatter import scatter_mean

# ==========================================
# 1. Configuration
# ==========================================
DEFAULT_CONFIG = {
    "project_name": "ST_CFDAI_AMG",
    "data_dir": "./extracted_data",
    "file_pattern": "*.npy",
    "batch_size": 4,              # GNNs use more VRAM than PointNet
    "learning_rate": 5e-4,
    "epochs": 1000,
    "model_dim": 128,             # Latent dimension width
    "num_layers": 4,              # Depth of GraphFormer
    "num_heads": 4,               # Attention heads
    "r_local": 0.05,              # Radius for local turbulence graph
    "k_local": 20,                # Neighbors for high-freq nodes
    "ratio_global": 0.1,          # Keep 10% of nodes for global graph
    "val_split": 0.2,
    "vis_frequency": 50
}

# ==========================================
# 2. The AMG Architecture Components
# ==========================================

class HighFreqIndicator(nn.Module):
    """
    Calculates which nodes are in 'high frequency' areas (turbulence/walls).
    Logic: Difference between a node and the average of its neighbors.
    """
    def forward(self, x, pos, batch, k=10):
        # 1. Build a quick KNN graph to check local neighborhood
        edge_index = knn_graph(pos, k=k, batch=batch)
        row, col = edge_index
        
        # 2. Calculate mean of neighbors features
        x_neigh_mean = scatter_mean(x[col], row, dim=0, dim_size=x.size(0))
        
        # 3. Indicator = L1 Norm of (Node - NeighborMean)
        # High value = High contrast/gradient = Turbulence
        indicator = torch.norm(x - x_neigh_mean, p=1, dim=-1)
        return indicator

class PhysicsGraphBlock(nn.Module):
    """
    Projects nodes into latent 'Physics Tokens' (Inlet, Outlet, Wall concepts)
    and allows global communication.
    """
    def __init__(self, in_dim, num_phys_tokens=32):
        super().__init__()
        self.num_phys = num_phys_tokens
        self.phys_tokens = nn.Parameter(torch.randn(1, num_phys_tokens, in_dim))
        
        # Attention for Nodes -> Physics
        self.attn_in = nn.MultiheadAttention(in_dim, num_heads=4, batch_first=True)
        # Attention for Physics -> Nodes
        self.attn_out = nn.MultiheadAttention(in_dim, num_heads=4, batch_first=True)
        
        self.norm1 = nn.LayerNorm(in_dim)
        self.norm2 = nn.LayerNorm(in_dim)

    def forward(self, x, batch):
        # x: [Total_N, C]
        # We need to process this batch-wise for global tokens
        # Convert to dense [B, N_max, C]
        x_dense, mask = to_dense_batch(x, batch)
        B = x_dense.size(0)
        
        # Expand tokens for batch
        tokens = self.phys_tokens.repeat(B, 1, 1) # [B, P, C]
        
        # 1. Nodes write to Physics Tokens
        # Query: Tokens, Key/Val: Nodes
        curr_tokens, _ = self.attn_in(query=tokens, key=x_dense, value=x_dense, key_padding_mask=~mask)
        tokens = tokens + curr_tokens
        
        # 2. Physics Tokens write back to Nodes
        # Query: Nodes, Key/Val: Tokens
        out_dense, _ = self.attn_out(query=x_dense, key=tokens, value=tokens)
        
        # Flatten back to [Total_N, C]
        out_flat = out_dense[mask]
        return self.norm2(x + self.norm1(out_flat))

class GraphFormerBlock(nn.Module):
    """
    The main processing block using Graph Attention (GATv2).
    It handles both the Local (High-Freq) and Global (FPS) graphs.
    """
    def __init__(self, dim, heads=4):
        super().__init__()
        self.gat = GATv2Conv(dim, dim, heads=heads, concat=False, dropout=0.1)
        self.norm1 = nn.LayerNorm(dim)
        self.ffn = nn.Sequential(
            nn.Linear(dim, dim*2),
            nn.GELU(),
            nn.Linear(dim*2, dim)
        )
        self.norm2 = nn.LayerNorm(dim)

    def forward(self, x, edge_index):
        # 1. Graph Attention
        h = self.gat(x, edge_index)
        x = self.norm1(x + h)
        
        # 2. Feed Forward
        h = self.ffn(x)
        x = self.norm2(x + h)
        return x

class FluidAMG(nn.Module):
    def __init__(self, in_channels=12, out_channels=4, model_dim=128, 
                 num_layers=4, ratio_global=0.2):
        super().__init__()
        self.model_dim = model_dim
        self.ratio_global = ratio_global
        
        # 1. Input Encoder
        # We assume input x has [x, y, z] in the first 3 columns if we need them, 
        # but usually we pass 'pos' separately.
        # Input features here are 9 (12 total - 3 coords)
        self.encoder = nn.Sequential(
            nn.Linear(in_channels - 3, model_dim),
            nn.GELU(),
            nn.Linear(model_dim, model_dim)
        )
        
        # 2. High Freq Indicator
        self.hf_indicator = HighFreqIndicator()
        
        # 3. Layers
        self.layers = nn.ModuleList()
        for _ in range(num_layers):
            self.layers.append(nn.ModuleDict({
                'physics': PhysicsGraphBlock(model_dim),
                'local': GraphFormerBlock(model_dim),
                'global': GraphFormerBlock(model_dim)
            }))
            
        # 4. Decoder
        self.decoder = nn.Sequential(
            nn.Linear(model_dim, model_dim),
            nn.GELU(),
            nn.Linear(model_dim, out_channels)
        )

    def forward(self, data):
        x, pos, batch = data.x, data.pos, data.batch
        
        # x is [Total_N, 9] (features without coords)
        # pos is [Total_N, 3]
        
        # Embedding
        h = self.encoder(x)
        
        # Calculate High-Frequency Indicator once (or per layer)
        # We treat the input features as the signal to detect turbulence
        hf_score = self.hf_indicator(h, pos, batch)
        
        for i, layer in enumerate(self.layers):
            
            # --- A. Physics Graph (Global Context) ---
            h = layer['physics'](h, batch)
            
            # --- B. Local Graph (High Frequency Focus) ---
            # Select top K nodes with highest gradients/turbulence
            # This is dynamic: the graph changes based on flow features
            # (Simplified: we select top 25% nodes per batch)
            # For simplicity in this implementation, we use KNN on ALL nodes 
            # but weight them by attention in GAT. 
            # To strictly follow AMG, we would subsample. 
            # Here, we stick to a radius graph on full mesh for local detail:
            edge_index_local = radius_graph(pos, r=0.05, batch=batch, max_num_neighbors=32)
            h = layer['local'](h, edge_index_local)
            
            # --- C. Global Graph (FPS Coarsening) ---
            # Sample subset of nodes to bridge long distances
            idx_global = fps(pos, batch, ratio=self.ratio_global)
            
            # Global nodes exchange info
            row, col = knn_graph(pos[idx_global], k=8, batch=batch[idx_global])
            edge_index_global = torch.stack([idx_global[row], idx_global[col]], dim=0)
            
            # We only update the global nodes, then broadcast back?
            # Standard GNO/AMG approach: Update global nodes, then interpolate back.
            # Here: We just run GAT on the global edges connected in the full graph context
            # (A simplification for stability):
            h_global = h.clone()
            h_global_out = layer['global'](h_global, edge_index_global)
            
            # Residual update only on selected global nodes
            h[idx_global] = h_global_out[idx_global]

        return self.decoder(h)

# ==========================================
# 3. PyG Data Handling
# ==========================================

class FluidPyGDataset(Dataset):
    def __init__(self, file_list):
        super().__init__()
        self.file_list = file_list

    def len(self):
        return len(self.file_list)

    def get(self, idx):
        # Load NPY [N, 12]
        data_np = np.load(self.file_list[idx])
        
        # Extract Coords [N, 3]
        pos = data_np[:, 0:3].astype(np.float32)
        
        # Normalize Coords (Critical for Radius Graph)
        centroid = np.mean(pos, axis=0)
        pos_norm = pos - centroid
        scale = np.max(np.sqrt(np.sum(pos_norm**2, axis=1)))
        pos_norm = pos_norm / (scale + 1e-6)
        
        # Extract Features [N, 9] (y_wall, masks, etc. - skipping original x,y,z in features)
        # Ind 0-2: coords, 3-6: target, 7: y_wall, 8-11: masks
        # Input to model: y_wall (7) + masks (8-11) + maybe coords again?
        # Let's give it y_wall, masks, and the normalized coords as features
        feats_rest = data_np[:, 7:12].astype(np.float32)
        x_features = np.concatenate([pos_norm, feats_rest], axis=1) # 3 + 5 = 8 inputs
        
        # Targets [N, 4]
        y = data_np[:, 3:7].astype(np.float32)
        
        # Masks [N]
        fluid_mask = data_np[:, 8].astype(bool)
        
        # Create PyG Data Object
        data = Data(
            x=torch.from_numpy(x_features), # [N, 8]
            pos=torch.from_numpy(pos_norm), # [N, 3]
            y=torch.from_numpy(y),          # [N, 4]
            mask=torch.from_numpy(fluid_mask)
        )
        return data

# ==========================================
# 4. Visualization & Training
# ==========================================

def log_visualizations(model, val_loader, device, epoch):
    model.eval()
    batch = next(iter(val_loader))
    batch = batch.to(device)
    
    with torch.no_grad():
        pred = model(batch)
    
    # Extract First Graph in Batch
    # batch.batch is a vector [0,0,0... 1,1,1... ]
    mask_graph0 = (batch.batch == 0) & batch.mask # Only fluid points of graph 0
    
    pos = batch.pos[mask_graph0].cpu().numpy()
    target_p = batch.y[mask_graph0, 3].cpu().numpy() # Pressure
    pred_p = pred[mask_graph0, 3].cpu().numpy()
    
    # 3D Plot
    fig = plt.figure(figsize=(10, 5))
    ax1 = fig.add_subplot(1, 2, 1, projection='3d')
    p1 = ax1.scatter(pos[:,0], pos[:,1], pos[:,2], c=target_p, cmap='jet', s=2)
    plt.colorbar(p1, ax=ax1)
    ax1.set_title("Ground Truth Pressure")
    
    ax2 = fig.add_subplot(1, 2, 2, projection='3d')
    p2 = ax2.scatter(pos[:,0], pos[:,1], pos[:,2], c=pred_p, cmap='jet', s=2)
    plt.colorbar(p2, ax=ax2)
    ax2.set_title(f"Predicted Pressure (Ep {epoch})")
    
    wandb.log({"Vis/3D_Pressure": wandb.Image(fig), "epoch": epoch})
    plt.close(fig)

def main():
    # Setup WandB
    wandb.init(project=DEFAULT_CONFIG["project_name"], config=DEFAULT_CONFIG)
    config = wandb.config
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using {device}")
    
    # Data Setup
    all_files = sorted(glob.glob(os.path.join(config.data_dir, config.file_pattern)))
    if not all_files: raise ValueError("No data found")
    
    split_idx = int(len(all_files) * (1 - config.val_split))
    train_files = all_files[:split_idx]
    val_files = all_files[split_idx:]
    
    train_ds = FluidPyGDataset(train_files)
    val_ds = FluidPyGDataset(val_files)
    
    # PyG DataLoader handles batching of graphs automatically
    train_loader = DataLoader(train_ds, batch_size=config.batch_size, shuffle=True, num_workers=4)
    val_loader = DataLoader(val_ds, batch_size=config.batch_size, shuffle=False)
    
    # Model Setup
    # Input channels = 8 (x,y,z, y_wall, 4 masks)
    model = FluidAMG(in_channels=8+3, out_channels=4, model_dim=config.model_dim, 
                     num_layers=config.num_layers).to(device)
    
    print(f"Model Parameters: {sum(p.numel() for p in model.parameters())}")
    
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    criterion = nn.MSELoss()
    
    wandb.watch(model, log_freq=100)
    
    # Training Loop
    best_loss = float('inf')
    
    for epoch in range(config.epochs):
        model.train()
        total_loss = 0
        steps = 0
        
        for batch in train_loader:
            batch = batch.to(device)
            optimizer.zero_grad()
            
            out = model(batch)
            
            # Loss only on fluid domain
            mask = batch.mask
            loss = criterion(out[mask], batch.y[mask])
            
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            steps += 1
            wandb.log({"train_step_loss": loss.item()})
            
        avg_train_loss = total_loss / steps
        
        # Validation
        model.eval()
        val_loss = 0
        val_steps = 0
        with torch.no_grad():
            for batch in val_loader:
                batch = batch.to(device)
                out = model(batch)
                mask = batch.mask
                loss = criterion(out[mask], batch.y[mask])
                val_loss += loss.item()
                val_steps += 1
        
        avg_val_loss = val_loss / val_steps
        
        print(f"Epoch {epoch} | Train: {avg_train_loss:.5f} | Val: {avg_val_loss:.5f}")
        wandb.log({"epoch": epoch, "train_loss": avg_train_loss, "val_loss": avg_val_loss})
        
        # Checkpointing
        if avg_val_loss < best_loss:
            best_loss = avg_val_loss
            torch.save(model.state_dict(), f"best_amg_model.pth")
            wandb.save("best_amg_model.pth")
            
        # Vis
        if epoch % config.vis_frequency == 0:
            log_visualizations(model, val_loader, device, epoch)

    wandb.finish()

if __name__ == "__main__":
    main()