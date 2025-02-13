import torch
from torch.nn.parallel.distributed import DistributedDataParallel

import lightning as L
from lightning.app.components import PyTorchSpawnMultiNode


class PyTorchDistributed(L.LightningWork):

    # Note: Only staticmethod are support for now with `PyTorchSpawnMultiNode`
    @staticmethod
    def run(
        world_size: int,
        node_rank: int,
        global_rank: str,
        local_rank: int,
    ):
        # 1. Prepare distributed model
        model = torch.nn.Linear(32, 2)

        # 2. Setup distributed training
        if torch.cuda.is_available():
            device = torch.device(f"cuda:{local_rank}")
            torch.cuda.set_device(device)
        else:
            device = torch.device("cpu")

        model = model.to(device)
        model = DistributedDataParallel(model, device_ids=[device.index] if torch.cuda.is_available() else None)

        # 3. Prepare loss and optimizer
        criterion = torch.nn.MSELoss()
        optimizer = torch.optim.SGD(model.parameters(), lr=0.01)

        # 4. Train the model for 50 steps.
        for step in range(50):
            model.zero_grad()
            x = torch.randn(64, 32).to(device)
            output = model(x)
            loss = criterion(output, torch.ones_like(output))
            print(f"global_rank: {global_rank} step: {step} loss: {loss}")
            loss.backward()
            optimizer.step()


# Run over 2 nodes of 4 x V100
app = L.LightningApp(
    PyTorchSpawnMultiNode(
        PyTorchDistributed,
        num_nodes=2,
        cloud_compute=L.CloudCompute("gpu-fast-multi"),  # 4 x V100
    )
)
