# Here are all the installs and imports you will need for your word cloud script and uploader widget
"""
!pip install wordcloud
!pip install fileupload
!pip install ipywidgets
!jupyter nbextension install --py --user fileupload
!jupyter nbextension enable --py fileupload
"""

from wordcloud import WordCloud
import numpy as np
from matplotlib import pyplot as plt
from IPython.display import display
import fileupload
import io
import sys

file_contents = "\"Well, maybe a little. But I didn't, because I thought-I didn't want things to stay the same for eternity, because things could always get better. And I was thinking . . .\" My throat felt really dry. \"Anyone in particular?\" Annabeth asked, her voice soft. I looked over and saw that she was trying not to smile. \"You're laughing at me,\" I complained. \"I am not!\" \"You are so not making this easy.\" Then she laughed for real, and she put her hands around my neck. \"I am never, ever going to make things easy for you, Seaweed Brain. Get used to it.\" When she kissed me, I had the feeling my brain was melting right through my body. I could've stayed that way forever, except a voice behind us growled, \"Well, it's about time!\" Suddenly the pavilion was filled with torchlight and campers. Clarisse led the way as the eavesdroppers charged and hoisted us both onto their shoulders. \"Oh, come on!\" I complained. \"Is there no privacy?\" \"The lovebirds need to cool off!\" Clarisse said with glee. \"The canoe lake!\" Connor Stoll shouted. With a huge cheer, they carried us down the hill, but they kept us close enough to hold hands. Annabeth was laughing, and I couldn't help laughing too, even though my face was completely red. We held hands right up to the moment they dumped us in the water. Afterward, I had the last laugh. I made an air bubble at the bottom of the lake. Our friends kept waiting for us to come up, but hey-when you're the son of Poseidon, you don't have to hurry. And it was pretty much the best underwater kiss of all time"

def calculate_frequencies(contents):
    frequency = {}
    # Here is a list of punctuations and uninteresting words you can use to process your text
    content = contents.split()
    punctuations = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''
    uninteresting_words = ["the", "a", "to", "if", "is", "it", "of", "and", "or", "an", "as", "i", "me", "my", \
    "we", "our", "ours", "you", "your", "yours", "he", "she", "him", "his", "her", "hers", "its", "they", "them", \
    "their", "what", "which", "who", "whom", "this", "that", "am", "are", "was", "were", "be", "been", "being", \
    "have", "has", "had", "do", "does", "did", "but", "at", "by", "with", "from", "here", "when", "where", "how", \
    "all", "any", "both", "each", "few", "more", "some", "such", "no", "nor", "too", "very", "can", "will", "just"]
    
    # LEARNER CODE START HERE
    
    
    for word in content:
        if word not in punctuations and word not in uninteresting_words:
            if word not in frequency:
                frequency[word] = 0
            frequency[word] += 1
    return frequency

# Display your wordcloud image
final_frequency = calculate_frequencies(file_contents)
cloud = WordCloud(width = 1000, height = 500).generate_from_frequencies(final_frequency)


plt.imshow(cloud)
