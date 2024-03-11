from bs4 import BeautifulSoup
from textblob import TextBlob
import pandas as pd
import requests
import os

def extract_text(url, uid):
	data = requests.get(url).text
	broth = BeautifulSoup(data, 'html.parser')
	soup = broth.find("article") if broth else ''
	title = soup.find("h1") if soup else '' 
	if title:
		title = title.get_text().strip()
	else:
		title = ""
	text = ''

	if soup: 
		for p in soup.find_all("p"):
			temp = p.get_text()
			text = text+(temp.strip())+' '
	else:
		text = ""
	
	
	f = open(f'./text/{uid}.txt', "w", encoding="utf-8")
	if(title):
		f.write(f'{title} {text}')
	else:
		f.write(f'{text}')
	f.close()
	
	return title, text

def syllable_count(word):
		word = word.lower()
		count = 0
		vowels = "aeiouy"
		if word[0] in vowels:
				count += 1
		for index in range(1, len(word)):
				if word[index] in vowels and word[index - 1] not in vowels:
						count += 1
		if word.endswith("e"):
				count -= 1
		if count == 0:
				count += 1
		return count

def analyze_text(text, pos, neg, stop):
	clean_text = " ".join([word.lower() for word in text.split() if word not in stop])
	blob = TextBlob(clean_text)

	positive_count = sum(word in pos for word in clean_text.split())
	negative_count = sum(word in neg for word in clean_text.split())


	def positive_score():
		return blob.sentiment.polarity+positive_count

	def negative_score():
		return blob.sentiment.polarity+negative_count

	def polarity_score():
		return (positive_score() - negative_score())/ ((positive_score() + negative_score()) + 0.000001)

	def subjectivity_score():
		if len(clean_text) > 0:
			return (positive_score() + negative_score()) / len(clean_text.split()) + 0.000001
		else:
			return 0
		
	
	# print(len(clean_text.split()), len(text.split()))

	def avg_sentence_length():
		if(len(blob.sentences) > 0):
			return sum(len(sentence.split()) for sentence in blob.sentences) / len(blob.sentences)
		else:
			return 0

	def percentage_complex_words():
		complex_words = [word for word in blob.words if syllable_count(word) >= 3]
		if(len(blob.words) > 0):
			return len(complex_words) / len(blob.words) * 100
		else:
			return 0

	def fog_index():
		sentences = len(blob.sentences)
		words = len(blob.words)
		characters = len(" ".join(blob.words))
		complex_words = sum(1 for word in blob.words if syllable_count(word) >= 3)
		if (len(blob.words) or len(blob.sentences)>0):
			return 0.4 * (words / sentences) + 100 * (complex_words / words)
		else:
			return 0

	def avg_number_words_per_sentence():
		return avg_sentence_length()

	def complex_word_count():
		complex_words = [word for word in blob.words if syllable_count(word) >= 3]
		return len(complex_words)

	def word_count():
		return len(blob.words)

	def syllable_per_word():
		if(word_count() > 0):
			return sum(syllable_count(word) for word in blob.words) / word_count()
		else:
			return 0
		

	def personal_pronouns():
		pronouns = blob.tags
		return sum(1 for token in pronouns if token[1] in ['PRP', 'PRP$'])

	def avg_word_length():
		if(word_count() > 0):
			return sum(len(word) for word in blob.words) / word_count()
		else:
			return 0

	
	variables = {
			'POSITIVE SCORE': positive_score(),
			'NEGATIVE SCORE': negative_score(),
			'POLARITY SCORE': polarity_score(),
			'SUBJECTIVITY SCORE': subjectivity_score(),
			'AVG SENTENCE LENGTH': avg_sentence_length(),
			'PERCENTAGE OF COMPLEX WORDS': percentage_complex_words(),
			'FOG INDEX': fog_index(),
			'AVG NUMBER OF WORDS PER SENTENCE': avg_number_words_per_sentence(),
			'COMPLEX WORD COUNT': complex_word_count(),
			'WORD COUNT': word_count(),
			'SYLLABLE PER WORD': syllable_per_word(),
			'PERSONAL PRONOUNS': personal_pronouns(),
			'AVG WORD LENGTH': avg_word_length()
	}

	return variables

def main():
	data = pd.read_excel('Input.xlsx')

	output_data = pd.DataFrame()

	def getwords(file):
		f = open(file, "r") 
		data = f.read() 
		data_into_list = data.split("\n") 
		f.close()
		return data_into_list

	def getstop(path):
		stoplist = []
		for file in os.listdir(path):
			stoplist.extend(getwords(os.path.join(path, file)))
		return stoplist

	
	poswords = getwords('./MasterDictionary/positive-words.txt')
	negwords = getwords('./MasterDictionary/negative-words.txt')
	stopwords = getstop('./StopWords/')

	for index, row in data.iterrows():
		url = row['URL']
		uid = row['URL_ID']

		title, text = extract_text(url, uid)

		variables = analyze_text(text, poswords, negwords, stopwords)

		row_data = {**row, **variables}

		output_data = output_data.append(row_data, ignore_index=True)
		output_data.to_excel('Output Data Structure.xlsx')
		print(f'File {index+1} - {row["URL_ID"]} pass')
	print('Output wrtitten to "Output Data Structure.xlsx"')

if __name__ == "__main__":
  main()