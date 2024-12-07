import os
import random
import soundfile as sf
import openl3
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from typing import Optional
import argparse

class EmbeddingVisualizer:
    def __init__(self, dataset_folder: str, model):
        """
        Initialize the visualizer with the dataset folder path.
        :param dataset_folder: Path to the GTZAN dataset folder.
        """
        self.dataset_folder = dataset_folder
        self.model = model
        self.embeddings = []
        self.labels = []

    def generate_embeddings(self, num_samples_per_genre: int = 10):
        """
        Generate embeddings for audio files in the dataset.
        :param num_samples_per_genre: Number of audio samples to process per genre.
        """
        genres = [genre for genre in os.listdir(self.dataset_folder) if os.path.isdir(os.path.join(self.dataset_folder, genre))]
        print(f"Found genres: {genres}")

        for genre in genres:
            genre_folder = os.path.join(self.dataset_folder, genre)
            files = [file for file in os.listdir(genre_folder) if file.endswith(('.wav', '.ogg', '.flac'))]

            # Randomly sample files from each genre
            sampled_files = random.sample(files, min(num_samples_per_genre, len(files)))
            print(f"Processing {len(sampled_files)} files from genre: {genre}")

            for file in sampled_files:
                file_path = os.path.join(genre_folder, file)
                print(f"Processing: {file_path}")

                # Read audio file
                audio, sr = sf.read(file_path)

                # Generate OpenL3 embeddings
                emb, ts = openl3.get_audio_embedding(audio, sr, model=self.model)
                self.embeddings.append(emb.mean(axis=0))  # Use mean embedding for simplicity
                self.labels.append(genre)

        print(f"Processed {len(self.embeddings)} audio files from all genres.")

    def plot_embeddings(
        self, 
        method: str = "pca", 
        save_path: Optional[str] = None
    ):
        """
        Visualize embeddings using PCA or t-SNE, coloring by genre.
        :param method: Dimensionality reduction method ('pca' or 'tsne').
        :param save_path: Path to save the plot. If None, the plot will be displayed.
        """
        if not self.embeddings:
            raise ValueError("No embeddings available. Run `generate_embeddings()` first.")

        embeddings_array = np.array(self.embeddings)

        if method == "pca":
            reducer = PCA(n_components=2)
            reduced_emb = reducer.fit_transform(embeddings_array)
        elif method == "tsne":
            n_samples = len(embeddings_array)
            perplexity = min(30, max(1, n_samples - 1))
            print(f"Using perplexity={perplexity} for t-SNE")
            reducer = TSNE(n_components=2, perplexity=perplexity, random_state=42)
            reduced_emb = reducer.fit_transform(embeddings_array)
        else:
            raise ValueError("Invalid method. Choose 'pca' or 'tsne'.")

        # Plot the embeddings
        plt.figure(figsize=(12, 10))
        genres = np.unique(self.labels)
        for genre in genres:
            idx = np.where(np.array(self.labels) == genre)[0]
            plt.scatter(reduced_emb[idx, 0], reduced_emb[idx, 1], label=genre, s=100, alpha=0.7)

        plt.title(f"Audio Embeddings Visualization ({method.upper()})")
        plt.xlabel("Dimension 1")
        plt.ylabel("Dimension 2")
        plt.legend(title="Genre", loc='best')
        plt.grid()

        # Save or display the plot
        if save_path:
            plt.savefig(save_path, format='png', dpi=300)
            print(f"Plot saved to {save_path}")
            plt.close()
        else:
            plt.show()


# Example usage python plot_openl3.py --dataset "./gtzan_dataset/genres_original/" --num_samples 1 --method "pca" --output "test1"
if __name__ == "__main__":
    # Argument parsing
    parser = argparse.ArgumentParser(description="Audio Embedding Visualizer")
    parser.add_argument("--dataset", type=str, required=True, help="Path to the dataset folder")
    parser.add_argument("--num_samples", type=int, default=10, help="Number of samples per genre to process")
    parser.add_argument("--method", type=str, choices=["pca", "tsne"], default="pca", help="Dimensionality reduction method")
    parser.add_argument("--output", type=str, default="results", help="Output folder for plots")
    args = parser.parse_args()

    # Load OpenL3 model
    model = openl3.models.load_audio_embedding_model(input_repr="mel128", content_type="music", embedding_size=6144)

    visualizer = EmbeddingVisualizer(args.dataset, model)
    visualizer.generate_embeddings(num_samples_per_genre=args.num_samples)

    # Create output folder and plot embeddings
    os.makedirs(args.output, exist_ok=True)
    visualizer.plot_embeddings(method=args.method, save_path=os.path.join(args.output, f"gtzan_{args.method}_result.png"))
