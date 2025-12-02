import re
from InstructorEmbedding import INSTRUCTOR
import torch
import torch.nn as nn
import numpy as np

# Define your neural network model
class ClassifierModel(nn.Module):
    def __init__(self, input_size, num_classes) -> None:
        """Model for downstream prediction after encoding"""
        super(ClassifierModel, self).__init__()
        self.fc1 = nn.Linear(input_size, 1024)
        self.fc2 = nn.Linear(1024, 512)
        self.fc3 = nn.Linear(512, num_classes)
    # end def

    def forward(self, x) -> torch.Tensor:
        """3 Layer Forward pass
        args:
            x (torch.Tensor): embeddings, size (1, input size)
        returns:
            x (torch.Tensor): classified, size 3
        """
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)
        return x
    # end def
# end class

class PromptClassifier:
    def __init__(self) -> None:
        # Initialize strings
        #self.warning = "Warning: Your prompt is known to produce responses which can be wrong or inaccurate. If you are using it for policy papers, speech writing, etc, we strongly recommend you to fact-check with other sources before using the responses."
        #self.soft_warning = "There may be a chance of hallucination with your request."
        #self.no_warning = "This task should not contain any hallucination."

        #self.mapping = {
        #    0: self.no_warning,
        #    1: self.warning,
        #    #2: self.soft_warning
        #}

        # Initialize model
        self.fp_prefix = "model"
        self.encoder = INSTRUCTOR(f"{self.fp_prefix}/instructor")
        embeddings_shape = 768
        self.classifier = ClassifierModel(embeddings_shape, 2)
        self.classifier.load_state_dict(torch.load(f"{self.fp_prefix}/nn/model_params.pth", map_location=torch.device('cpu')))
        self.classifier.eval()
    
    def contains_url(self, text) -> bool:
        # Regular expression to match URLs
        url_pattern = re.compile(r'https?://\S+|www\.\S+')

        # Use findall to search for URL patterns in the text
        urls = re.findall(url_pattern, text)

        # If any URLs are found, return True; otherwise, return False
        return bool(urls)
    # end def

    def first_cut_classification(self, text) -> str:
        if self.contains_url(text):
            return "1"
        
        if ((len(text.split(' ')) < 3) or len(text) < 10):
            return "0"
    # end def
           
    def predict(self, text) -> str:
        embeddings = torch.tensor(self.encoder.encode([text]))
        with torch.no_grad():
            outputs = self.classifier.forward(embeddings)
        prediction = torch.argmax(outputs, dim=1).cpu().numpy()[0]
        
        #return self.mapping[int(prediction)]
        return str(prediction)
    # end def
    #     
    def process_long_string(self, input_str) -> str:
        max_length = 512
        target_length = 256

        # If the string is already within or equal to the target length, return it as is
        if len(input_str) <= max_length:
            return input_str

        # Take the first 512 characters
        first_half = input_str[:target_length]

        # Find the index of the last '.' within the last 512 characters
        last_dot_index = first_half.rfind('.')

        # If there's no '.', use the last character of the first half
        if last_dot_index == -1:
            last_dot_index = target_length - 1

        # Take the second half starting from the last '.' (or the last character if no '.')
        second_half = input_str[-(target_length - last_dot_index):]

        # Combine the first and second halves with '...' in between
        result_str = first_half[:last_dot_index] + '.' + second_half

        return result_str
    # end def

    def create_embeddings(self, text):
        embeddings = self.encoder.encode([text]).tolist()
        return embeddings
    # end def

    def run_pipeline(self, text):
        outcome = self.first_cut_classification(text)
        if outcome:
            return outcome
        else:
            text = self.process_long_string(text)
            return self.predict(text)
    # end def
# end class