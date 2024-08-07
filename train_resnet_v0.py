import os

import torch
import torch.optim as optim

from tqdm import tqdm
from data import get_dataloader

import hydra
import logging
from hydra.utils import to_absolute_path
from omegaconf import DictConfig
from torch.utils.tensorboard import SummaryWriter

from model import *
import warnings
warnings.filterwarnings("ignore")

log = logging.getLogger(__name__)

def train(model, dataset, log_dir, data_dir, n_classes, in_channel, ck_dir, n_epoch, 
          lr, batch_size, weight_decay, aug_type):
    """
    Trains the specified model on the given dataset and logs the training process.
    """
    writer = SummaryWriter(log_dir=log_dir)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = ResNet18(num_classes=n_classes, in_channels=in_channel).to(device)

    trainloader, valloader = get_dataloader(data_dir=data_dir, dataset=dataset,
                                            batch_size=batch_size,
                                            train=True, val=True,
                                            aug_type=aug_type)

    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
    criterion = nn.NLLLoss()

    for epoch in range(n_epoch):
        epoch_loss = 0.
        epoch_loss_val = 0.

        model.train()
        with tqdm(total=len(trainloader), desc=f'Training Epoch {epoch+1}/{n_epoch}') as pbar:
            for batch_id, (imgs, labels) in enumerate(trainloader):
                imgs, labels = imgs.to(device), labels.to(device)
                pred = model(imgs)

                loss = criterion(pred, labels)

                epoch_loss += loss

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                pbar.set_postfix({'Loss': f'{epoch_loss.item()/(batch_id+1):.4f}'})
                pbar.update()

        model.eval()
        with torch.no_grad():
            with tqdm(total=len(valloader), desc=f'Validation Epoch {epoch+1}/{n_epoch}') as pbar:
                for batch_id, (imgs, labels) in enumerate(valloader):
                    imgs, labels = imgs.to(device), labels.to(device)
                    pred = model(imgs)

                    loss_val = criterion(pred, labels)

                    epoch_loss_val += loss_val

                    pbar.set_postfix({'Loss_val': f'{epoch_loss_val.item()/(1+batch_id):.4f}'})
                    pbar.update()

        writer.add_scalars('Loss', {'train': epoch_loss/len(trainloader), 'val': epoch_loss_val/len(valloader)}, epoch)

        if (epoch+1) % 50 == 0:
            ck_path = os.path.join(ck_dir, f'resnet18_epoch{epoch+1}.pt')
            torch.save(model.state_dict(), ck_path)
            log.info(f'Saved checkpoint: {ck_path}')

    ck_path_final = os.path.join(ck_dir, f'resnet18_epoch{n_epoch}.pt')
    torch.save(model.state_dict(), ck_path_final)
    log.info('Training Done')
    writer.close()

@hydra.main(config_path='conf_resnet18', config_name='train_v0_config')
def main(cfg: DictConfig):
    experiment_name = cfg.experiment.name
    log_dir = cfg.experiment.log_dir
    seed =cfg.experiment.seed
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    model = cfg.model.name
    ck_dir = to_absolute_path(cfg.model.ck_dir)
    os.makedirs(ck_dir, exist_ok=True)

    dataset_name =cfg.dataset.name
    datadir = to_absolute_path(cfg.dataset.dir)
    n_classes = cfg.dataset.n_classes
    in_channel = cfg.dataset.in_channel

    batch_size = cfg.params.batch_size
    lr = cfg.params.lr
    n_epoch = cfg.params.n_epoch
    weight_decay = cfg.params.weight_decay
    aug_type = cfg.params.aug_type

    log.info(f'Experiment: {experiment_name}')
    log.info(f'Device: {device}')
    log.info(f'Seed: {seed}')
    log.info(f'log_dir: {log_dir}')

    log.info(f'Dataset: {dataset_name}')
    log.info(f'clean_data directory: {datadir}') 
    log.info(f'n_classes: {n_classes}')
    log.info(f'in_channel: {in_channel}')
    
    log.info(f'Model: {model}')
    log.info(f'ck_dir: {ck_dir}')

    log.info(f'Training with')
    log.info(f'batch size: {batch_size}')
    log.info(f'learning rate: {lr}')
    log.info(f'epochs: {n_epoch}')
    log.info(f'data augmentation: {aug_type}')
    log.info(f'weight decay: {weight_decay}')

    torch.manual_seed(seed)
    train(model=model,
          dataset=dataset_name,
          log_dir=log_dir,
          data_dir=datadir,
          n_classes=n_classes,
          in_channel=in_channel,
          ck_dir=ck_dir,
          n_epoch=n_epoch,
          lr=lr,
          batch_size=batch_size,
          weight_decay=weight_decay,
          aug_type=aug_type,)

if __name__ == "__main__":    
    main()

