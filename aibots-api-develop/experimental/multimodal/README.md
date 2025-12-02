# How to process image, text, audio and video intto GPT4o 

Last Updated Jul 2024

# Preprocessing Audio and Video

GPT4o on Azure has access to both text and speech inputs only

To perform audio (speech only) inputs, transcribe the audio to text. This can be done using STT model like Whisper (via OpenAI Azure as well)

To perform video inputs, read the frames of the videos as image. As GPT4-o can only take in maximum 10 frames per call, we should either

Pick image every x frame (x being total frames // 10)

Sample uniformly until you have 10 frames

Perform clustering on all the frames for 10 cluster centers

Clustering can be done 1) Performing embeddings (using models like Vit Transformers) 2) Utilizing clustering algorithms like Kmeans or DBScan for 10 representative clusters


# Cleaning Audio and Video

TODO

# Benchmarking Clustering and Embeddings Algorithm

TODO

# 