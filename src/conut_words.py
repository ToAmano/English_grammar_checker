import argparse
import re
from collections import Counter
import string

def strip_latex_commands(text):
    # LaTeXコマンド（\command{...}や\command）を除去
    text = re.sub(r'\\[a-zA-Z]+\{.*?\}', '', text)
    text = re.sub(r'\\[a-zA-Z]+\s*', '', text)
    text = re.sub(r'\$.*?\$', '', text)  # 数式部分 ($...$) も除去
    text = re.sub(r'\{.*?\}', '', text)  # 残った中括弧を除去
    return text

from nltk import pos_tag, word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
import nltk
nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger_eng')
nltk.download('wordnet')

lemmatizer = WordNetLemmatizer()

def get_wordnet_pos(treebank_tag):
    # NLTKの品詞タグをWordNetの品詞タグに変換
    if treebank_tag.startswith('J'):
        return wordnet.ADJ
    elif treebank_tag.startswith('V'):
        return wordnet.VERB
    elif treebank_tag.startswith('N'):
        return wordnet.NOUN
    elif treebank_tag.startswith('R'):
        return wordnet.ADV
    else:
        return wordnet.NOUN  # デフォルトは名詞

def lemmatize_words(words):
    tagged = pos_tag(words)
    return [lemmatizer.lemmatize(word, get_wordnet_pos(tag)) for word, tag in tagged]


def count_word_frequencies(lines):
    all_words = []
    for line in lines:
        # コメント（%以降）を削除
        line = line.split('%')[0]
        text = strip_latex_commands(line)
        # 小文字化し、句読点を除去して単語を分割
        text = text.lower().translate(str.maketrans('', '', string.punctuation))
        # words = text.split()
        # all_words.extend(words)
        words = word_tokenize(text)
        lemmas = lemmatize_words(words)
        all_words.extend(lemmas)
        
    
    return Counter(all_words)

def main():
    parser = argparse.ArgumentParser(description="LaTeXファイル内の単語出現頻度を集計")
    parser.add_argument("filename", help="LaTeXファイル名")
    args = parser.parse_args()

    with open(args.filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    counter = count_word_frequencies(lines)

    print("\n📊 単語の出現頻度:")
    for word, freq in counter.most_common():
        print(f"{word}: {freq}")

if __name__ == "__main__":
    main()
