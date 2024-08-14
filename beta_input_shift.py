import torch
import torch.nn.functional as F
import matplotlib.pyplot as plt
import numpy as np
from model import *
from data import get_dataloader
from utils import unnormalize
import os
import warnings

warnings.filterwarnings("ignore")

# Define CIFAR-10 class names
class_names = ['airplane', 'automobile', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse', 'ship', 'truck']

def generate_noise(img, unet_ck_path, in_channels):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    unet = UNet(in_channels=in_channels, out_channels=in_channels).to(device)
    model_dict = torch.load(unet_ck_path)
    unet.load_state_dict(model_dict)
    unet.eval()

    img = img.to(device)
    with torch.no_grad():
        img_noisy = unet(img)
    
    return img_noisy

def get_predictions(model, img):
    model.eval()
    with torch.no_grad():
        outputs = model(img)
        probabilities = F.softmax(outputs, dim=1).cpu().numpy()
    return probabilities

def main():
    torch.manual_seed(2333)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    input_dir = './data/CIFAR10'
    in_channels = 3
    unet_ck_dir = './checkpoints/beta'
    beta_values = [0.5, 0.8, 1.0, 1.5]  # Different beta values to evaluate
    batch_size = 2

    dataloader = get_dataloader(data_dir=input_dir, train=True, val=False, batch_size=batch_size)
    imgs, labels = next(iter(dataloader))
    imgs, labels = imgs.to(device), labels.to(device)

    # Load ResNet18 model
    resnet18 = ResNet18(num_classes=10).to(device)
    resnet_ck_path = './checkpoints/resnet18_v0/resnet18_epoch300.pt'
    resnet18.load_state_dict(torch.load(resnet_ck_path))

    # Unnormalize and convert the original images for plotting
    imgs_original = unnormalize(imgs).permute(0, 2, 3, 1).cpu().numpy()

    fig, axs = plt.subplots(batch_size, len(beta_values) + 3, figsize=(20, 10))  # Extra columns for clean and mean predictions

    for idx in range(batch_size):
        class_name = class_names[labels[idx].item()]

        axs[idx, 0].imshow(imgs_original[idx])
        axs[idx, 0].set_title(f'Original: {class_name}')
        axs[idx, 0].axis('off')

        # Get predictions for the clean image
        clean_probs = get_predictions(resnet18, imgs[idx].unsqueeze(0))

        # Plot the clean image prediction probabilities as a bar chart
        axs[idx, 1].barh(class_names, clean_probs[0], color='lightgreen')
        if idx == 0:
            axs[idx, 1].tick_params(axis='y', labelrotation=60)  # Rotate the class names by 45 degrees
        else:
            axs[idx, 1].get_yaxis().set_visible(False)
        axs[idx, 1].set_xlim(0, 1)
        axs[idx, 1].set_xticks([])

        all_probs = []

        for i, beta in enumerate(beta_values):
            unet_ck_path = os.path.join(unet_ck_dir, f'beta_{beta}.pt')
            img_noisy = generate_noise(imgs[idx].unsqueeze(0), unet_ck_path, in_channels)

            # Plot the noisy image generated by UNet for each beta value
            img_noisy_unnorm = unnormalize(img_noisy).permute(0, 2, 3, 1).cpu().numpy()
            axs[idx, i + 2].imshow(img_noisy_unnorm[0])
            if idx == 0:
                axs[idx, i + 2].set_title(f'Beta {beta}')
            axs[idx, i + 2].axis('off')

            # Get predictions for the noisy image
            probs = get_predictions(resnet18, img_noisy)
            all_probs.append(probs[0])

        # Calculate the mean of predictions over all noisy images
        mean_probs = np.mean(all_probs, axis=0)

        # Plot the mean prediction probabilities as a bar chart
        axs[idx, -1].barh(class_names, mean_probs, color='skyblue')
        if idx == 0:
            axs[idx, -1].tick_params(axis='y', labelrotation=60)  # Rotate the class names by 45 degrees
        else:
            axs[idx, -1].get_yaxis().set_visible(False)
        axs[idx, -1].set_xlim(0, 1)
        axs[idx, -1].set_xticks([])

    # plt.tight_layout()
    plt.savefig(f'./plot_results/input_shift_grid_with_clean_and_mean_predictions.png')
    plt.show()

if __name__ == '__main__':
    main()
