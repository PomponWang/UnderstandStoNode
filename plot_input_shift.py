import torch
import matplotlib.pyplot as plt
from model import *
from data import get_dataloader
from utils import unnormalize
import os
import warnings

warnings.filterwarnings("ignore")

# Define CIFAR-10 class names
class_names = ['airplane', 'automobile', 'bird', 'cat', 'deer', 
               'dog', 'frog', 'horse', 'ship', 'truck']

def generate_noise(img, unet_ck_path, in_channels):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    unet = UNet(in_channels=in_channels, out_channels=in_channels).to(device)
    model_dict = torch.load(unet_ck_path)
    unet.load_state_dict(model_dict)
    unet.eval()

    img = img.to(device)
    with torch.no_grad():
        img_noisy = unet(img)
    
    img_noisy = unnormalize(img_noisy).permute(0, 2, 3, 1).cpu().numpy()
    return img_noisy

def main():
    torch.manual_seed(42)
    input_dir = './data/CIFAR10'
    in_channels = 3
    unet_ck_dir = './checkpoints/unet'
    epochs = range(80, 101, 10) 
    batch_size = 4  # Load 4 images to create a 2x2 grid

    # Load a batch of images from the dataset
    dataloader = get_dataloader(data_dir=input_dir, train=True, val=False, batch_size=batch_size)
    imgs, labels = next(iter(dataloader))

    # Unnormalize and convert the original images for plotting
    imgs_original = unnormalize(imgs).permute(0, 2, 3, 1).cpu().numpy()

    fig, axs = plt.subplots(batch_size, len(epochs) + 1, figsize=(18, 12))

    for idx in range(batch_size):
        class_name = class_names[labels[idx].item()]

        # Plot the original image in the first column
        axs[idx, 0].imshow(imgs_original[idx])
        if idx == 0:
            axs[idx, 0].set_title(f'Original: {class_name}')
        else:
            axs[idx, 0].set_title(f'{class_name}')
        axs[idx, 0].axis('off')

        for i, epoch in enumerate(epochs):
            unet_ck_path = os.path.join(unet_ck_dir, f'unet_epoch{epoch}.pt')
            img_noisy = generate_noise(imgs[idx].unsqueeze(0), unet_ck_path, in_channels)

            # Plot the noisy image generated by UNet at each epoch
            axs[idx, i + 1].imshow(img_noisy[0])
            if idx == 0:  # Only label epochs on the first row
                axs[idx, i + 1].set_title(f'Epoch {epoch}')
            axs[idx, i + 1].axis('off')

    plt.suptitle('Input Shift')
    plt.tight_layout()
    plt.savefig(f'./plot_results/input_shift_grid.png')
    plt.show()

if __name__ == '__main__':
    main()
