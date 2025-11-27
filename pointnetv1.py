import datetime
import os
import glob
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import wandb
import matplotlib
matplotlib.use('Agg') # Non-interactive backend for server
import matplotlib.pyplot as plt
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split

# ==========================================
# 1. Configuration & WandB Init
# ==========================================

# Default Hyperparameters
DEFAULT_CONFIG = {
    "project_name": "ST_CFDAI",
    "data_dir": "./extracted_data",
    "file_pattern": "*.npy",
    "batch_size": 8,
    "learning_rate": 1e-4,
    "epochs": 1000,
    "architecture": "PointnetCFD",
    "scaling": 0.25,            # Controls model width
    "val_split": 0.2,           # 20% validation
    "vis_frequency": 100,       # Log 3D plots every N epochs
    "num_workers": 10,          # cpu core count
    "input_channels": 8,        # x,y,z, y_wall, masks...
    "output_channels": 4        # u,v,w,p
}

# ==========================================
# 2. Data Loading (Same as before)
# ==========================================

class FluidDataset(Dataset):
    def __init__(self, file_list, load_to_ram=False):
        self.file_list = file_list
        self.load_to_ram = load_to_ram
        self.data_cache = []

        if self.load_to_ram:
            print(f"Loading {len(file_list)} files into RAM...")
            for f in file_list:
                self.data_cache.append(np.load(f))

    def __len__(self):
        return len(self.file_list)

    def __getitem__(self, idx):
        # Load data: N x 12
        if self.load_to_ram:
            sample = self.data_cache[idx]
        else:
            sample = np.load(self.file_list[idx])

        # Preprocessing
        coords = sample[:, 0:3]
        
        # Normalize coords locally to [-1, 1] (Standard PointNet practice)
        centroid = np.mean(coords, axis=0)
        coords = coords - centroid
        m = np.max(np.sqrt(np.sum(coords ** 2, axis=1)))
        coords = coords / (m + 1e-6)

        # Features: y_wall (7) + masks (8,9,10,11)
        features = sample[:, 7:12] 
        
        # Inputs: [8, N]
        x_in = np.concatenate([coords, features], axis=1).astype(np.float32)
        x_in = x_in.transpose(1, 0) 

        # Targets: u, v, w, p (3,4,5,6) -> [4, N]
        y_out = sample[:, 3:7].astype(np.float32)
        y_out = y_out.transpose(1, 0) 
        
        # Fluid Mask: Index 8
        fluid_mask = sample[:, 8].astype(bool)
        
        return torch.from_numpy(x_in), torch.from_numpy(y_out), torch.from_numpy(fluid_mask)

def collate_fn_pad(batch):
    inputs = [b[0] for b in batch]
    targets = [b[1] for b in batch]
    fluid_masks = [b[2] for b in batch]

    batch_size = len(batch)
    max_len = max([t.shape[1] for t in inputs])
    n_in = inputs[0].shape[0]
    n_out = targets[0].shape[0]

    padded_inputs = torch.zeros(batch_size, n_in, max_len)
    padded_targets = torch.zeros(batch_size, n_out, max_len)
    padded_fluid_masks = torch.zeros(batch_size, max_len, dtype=torch.bool)
    padding_mask = torch.zeros(batch_size, max_len, dtype=torch.bool)

    for i in range(batch_size):
        length = inputs[i].shape[1]
        padded_inputs[i, :, :length] = inputs[i]
        padded_targets[i, :, :length] = targets[i]
        padded_fluid_masks[i, :length] = fluid_masks[i]
        padding_mask[i, :length] = 1 

    return padded_inputs, padded_targets, padded_fluid_masks, padding_mask

# ==========================================
# 3. Model (PointNet)
# ==========================================

class PointNetFluid(nn.Module):
    def __init__(self, input_channels=8, output_channels=4, scaling=1.0):
        super(PointNetFluid, self).__init__()
        
        s = scaling
        self.conv1 = nn.Conv1d(input_channels, int(64*s), 1)
        self.bn1 = nn.BatchNorm1d(int(64*s))
        self.conv2 = nn.Conv1d(int(64*s), int(64*s), 1)
        self.bn2 = nn.BatchNorm1d(int(64*s))
        
        self.conv3 = nn.Conv1d(int(64*s), int(64*s), 1)
        self.bn3 = nn.BatchNorm1d(int(64*s))
        self.conv4 = nn.Conv1d(int(64*s), int(128*s), 1)
        self.bn4 = nn.BatchNorm1d(int(128*s))
        self.conv5 = nn.Conv1d(int(128*s), int(1024*s), 1)
        self.bn5 = nn.BatchNorm1d(int(1024*s))

        self.conv6 = nn.Conv1d(int(1024*s) + int(64*s), int(512*s), 1)
        self.bn6 = nn.BatchNorm1d(int(512*s))
        self.conv7 = nn.Conv1d(int(512*s), int(256*s), 1)
        self.bn7 = nn.BatchNorm1d(int(256*s))
        self.conv8 = nn.Conv1d(int(256*s), int(128*s), 1)
        self.bn8 = nn.BatchNorm1d(int(128*s))
        self.conv9 = nn.Conv1d(int(128*s), output_channels, 1)

    def forward(self, x, padding_mask=None):
        num_points = x.size(-1)

        x = F.relu(self.bn1(self.conv1(x)))
        x = F.relu(self.bn2(self.conv2(x)))
        local_feature = x 

        x = F.relu(self.bn3(self.conv3(x)))
        x = F.relu(self.bn4(self.conv4(x)))
        x = F.relu(self.bn5(self.conv5(x)))

        if padding_mask is not None:
            mask_expanded = padding_mask.unsqueeze(1).expand_as(x)
            x_masked = x.masked_fill(~mask_expanded, float('-inf'))
            global_feature = F.max_pool1d(x_masked, kernel_size=num_points)
        else:
            global_feature = F.max_pool1d(x, kernel_size=num_points)
            
        global_feature = global_feature.expand(-1, -1, num_points)
        x = torch.cat([local_feature, global_feature], dim=1)

        x = F.relu(self.bn6(self.conv6(x)))
        x = F.relu(self.bn7(self.conv7(x)))
        x = F.relu(self.bn8(self.conv8(x)))
        
        x = self.conv9(x)
        return x

# ==========================================
# 4. Visualization Utilities
# ==========================================

def create_comparison_plot(coords, target, pred, title_prefix):
    """
    Creates a matplotlib figure comparing Target vs Pred in 3D
    coords: [N, 3]
    target: [N] (Scalar field, e.g., Pressure)
    pred: [N] (Scalar field)
    """
    fig = plt.figure(figsize=(12, 5))
    
    # Plot Target
    ax1 = fig.add_subplot(1, 2, 1, projection='3d')
    sc1 = ax1.scatter(coords[:,0], coords[:,1], coords[:,2], c=target, cmap='jet', s=2)
    ax1.set_title(f"{title_prefix} - Ground Truth")
    plt.colorbar(sc1, ax=ax1)
    
    # Plot Prediction
    ax2 = fig.add_subplot(1, 2, 2, projection='3d')
    sc2 = ax2.scatter(coords[:,0], coords[:,1], coords[:,2], c=pred, cmap='jet', s=2)
    ax2.set_title(f"{title_prefix} - Prediction")
    plt.colorbar(sc2, ax=ax2)
    
    plt.tight_layout()
    return fig

def log_visualizations(model, val_loader, device, epoch):
    """
    Takes one batch from val_loader, predicts, and logs 3D plots to WandB
    """
    model.eval()
    try:
        inputs, targets, fluid_masks, padding_mask = next(iter(val_loader))
    except StopIteration:
        return

    inputs, targets = inputs.to(device), targets.to(device)
    padding_mask = padding_mask.to(device)
    
    with torch.no_grad():
        preds = model(inputs, padding_mask)

    # Take the first sample in the batch
    idx = 0
    # Extract valid points only (remove padding)
    mask = padding_mask[idx].cpu().numpy().astype(bool)
    
    # Inputs: [8, N] -> [N, 8] -> extract coords [N, 0:3]
    coords = inputs[idx].cpu().numpy().transpose(1, 0)[mask, 0:3]
    
    # Targets/Preds: [4, N] -> [N, 4] -> u,v,w,p
    y_true = targets[idx].cpu().numpy().transpose(1, 0)[mask, :]
    y_pred = preds[idx].cpu().numpy().transpose(1, 0)[mask, :]

    # 1. Compare Pressure (Index 3)
    fig_p = create_comparison_plot(coords, y_true[:, 3], y_pred[:, 3], "Pressure")
    
    # 2. Compare Velocity Magnitude (Indices 0,1,2)
    vel_mag_true = np.sqrt(y_true[:,0]**2 + y_true[:,1]**2 + y_true[:,2]**2)
    vel_mag_pred = np.sqrt(y_pred[:,0]**2 + y_pred[:,1]**2 + y_pred[:,2]**2)
    fig_v = create_comparison_plot(coords, vel_mag_true, vel_mag_pred, "Velocity Mag")

    # Log Images
    wandb.log({
        "Vis/Pressure_Comparison": wandb.Image(fig_p),
        "Vis/Velocity_Comparison": wandb.Image(fig_v),
        "epoch": epoch
    })
    
    plt.close(fig_p)
    plt.close(fig_v)

# ==========================================
# 5. Main Training Loop
# ==========================================

def get_file_list(config):
    pattern = os.path.join(config.data_dir, config.file_pattern)
    files = sorted(glob.glob(pattern))
    if not files:
        raise ValueError(f"No files found in {pattern}")
    return files

def main():
    # 1. Initialize WandB
    date = datetime.datetime.today().strftime("%Y_%m_%d_%H:%M:%S")
    wandb.init(project=DEFAULT_CONFIG["project_name"], config=DEFAULT_CONFIG)
    config = wandb.config # Allow wandb sweeps to override defaults

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Running on {device}")

    # 2. Prepare Data
    all_files = get_file_list(config)
    train_files, val_files = train_test_split(all_files, test_size=config.val_split, random_state=42)
    
    train_ds = FluidDataset(train_files)
    val_ds = FluidDataset(val_files)

    train_loader = DataLoader(train_ds, batch_size=config.batch_size, shuffle=True, 
                              collate_fn=collate_fn_pad, num_workers=config.num_workers)
    val_loader = DataLoader(val_ds, batch_size=config.batch_size, shuffle=False, 
                            collate_fn=collate_fn_pad, num_workers=config.num_workers)

    # 3. Model Setup
    model = PointNetFluid(input_channels=config.input_channels, 
                          output_channels=config.output_channels, 
                          scaling=config.scaling).to(device)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    criterion = nn.MSELoss(reduction='none')

    # Magic: Log gradients and model topology
    wandb.watch(model, log="all", log_freq=100)
    
    best_val_loss = float('inf')

    # 4. Training Loop
    print("Starting training...")
    for epoch in range(config.epochs):
        model.train()
        train_loss_accum = 0.0
        points_count = 0
        
        for batch_idx, (inputs, targets, fluid_masks, padding_mask) in enumerate(train_loader):
            inputs, targets = inputs.to(device), targets.to(device)
            fluid_masks, padding_mask = fluid_masks.to(device), padding_mask.to(device)
            
            optimizer.zero_grad()
            outputs = model(inputs, padding_mask)

            # Masked Loss
            valid_mask = fluid_masks & padding_mask
            loss_raw = criterion(outputs, targets)
            masked_loss = loss_raw.mean(dim=1)[valid_mask]
            
            if masked_loss.numel() > 0:
                loss = masked_loss.mean()
                loss.backward()
                optimizer.step()
                
                # Log batch metrics
                current_loss = loss.item()
                train_loss_accum += current_loss
                points_count += 1
                
                # Log Step-wise
                wandb.log({"train_batch_loss": current_loss})

        avg_train_loss = train_loss_accum / max(points_count, 1)

        # Validation
        model.eval()
        val_loss_accum = 0.0
        val_count = 0
        with torch.no_grad():
            for inputs, targets, fluid_masks, padding_mask in val_loader:
                inputs, targets = inputs.to(device), targets.to(device)
                fluid_masks, padding_mask = fluid_masks.to(device), padding_mask.to(device)

                outputs = model(inputs, padding_mask)
                
                valid_mask = fluid_masks & padding_mask
                loss_raw = criterion(outputs, targets)
                masked_loss = loss_raw.mean(dim=1)[valid_mask]

                if masked_loss.numel() > 0:
                    val_loss_accum += masked_loss.mean().item()
                    val_count += 1

        avg_val_loss = val_loss_accum / max(val_count, 1)

        # Log Epoch Metrics
        wandb.log({
            "epoch": epoch,
            "train_loss": avg_train_loss,
            "val_loss": avg_val_loss,
            "learning_rate": optimizer.param_groups[0]['lr']
        })

        print(f"Epoch {epoch} | Train: {avg_train_loss:.6f} | Val: {avg_val_loss:.6f}")

        # Checkpointing
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            
            file_name = f"weights/best_pointnet_fluid_{date}.pth"
            torch.save(model.state_dict(), file_name)
            wandb.save("best_model.pth") # Upload to cloud

        # Visualization (Every N epochs)
        if epoch % config.vis_frequency == 0:
            print("Generating 3D Visualizations...")
            log_visualizations(model, val_loader, device, epoch)

    wandb.finish()

if __name__ == "__main__":
    main()
