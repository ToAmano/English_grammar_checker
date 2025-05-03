import re
import spacy
import argparse

nlp = spacy.load("en_core_web_sm")

def extract_english_text_from_tex(tex_file):
    with open(tex_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # LaTeXコマンドや数式を除去
    content = re.sub(r'\\[a-zA-Z]+\{.*?\}', '', content)  # \command{...}
    content = re.sub(r'\\[a-zA-Z]+\s*', '', content)       # \command
    content = re.sub(r'\$.*?\$', '', content)              # inline math
    content = re.sub(r'\{.*?\}', '', content)              # {...}
    content = re.sub(r'%.*', '', content)                  # comments

    # 英文のみに近い行を抽出（アルファベット中心の行）
    lines = content.splitlines()
    english_lines = [line.strip() for line in lines if re.search(r'[a-zA-Z]{3,}', line)]
    return english_lines

def check_subject_verb_agreement(lines):
    modal_verbs = {"can", "could", "may", "might", "shall", "should", "will", "would", "must"}
    third_person_singular_pronouns = {"he", "she", "it"}

    for line in lines:
        doc = nlp(line)

        for token in doc:
            if token.dep_ == "nsubj":
                # 主語が三単現の可能性があるかどうか
                if token.tag_ in ("NN", "NNP"):
                    is_third_singular = True
                elif token.tag_ == "PRP":
                    is_third_singular = token.text.lower() in third_person_singular_pronouns
                else:
                    is_third_singular = False

                if not is_third_singular:
                    continue

                verb = token.head

                if verb.pos_ != "VERB":
                    continue

                # 過去形や過去分詞なら除外
                if verb.tag_ in ("VBD", "VBN"):
                    continue

                # 助動詞（should, could, etc.）があるなら除外
                if any(child.text.lower() in modal_verbs and child.dep_ == "aux" for child in verb.children):
                    continue

                # 自身が助動詞なら除外
                if verb.text.lower() in modal_verbs:
                    continue

                # 「does not 動詞」パターン（否定）を除外
                has_does_not = any(
                    child.text.lower() == "does" and child.dep_ == "aux" and
                    any(sib.text.lower() == "not" for sib in child.head.children)
                    for child in verb.children
                )
                if has_does_not:
                    continue

                # 三単現なのに原形（sなし）を使っていれば警告
                if verb.tag_ in ("VB", "VBP"):
                    print(f"⚠️ 三単現の's'の疑い: 「{line}」")
                    print(f"   主語: '{token.text}'（{token.tag_}） → 動詞: '{verb.text}'（{verb.tag_}）\n")
# def check_subject_verb_agreement(lines):
#     for line in lines:
#         doc = nlp(line)
#         for token in doc:
#             # 主語が単数の名詞または代名詞 (he, she, it, Johnなど)
#             if token.dep_ == "nsubj" and token.tag_ in ("NN", "NNP", "PRP"):
#                 subj = token
#                 verb = token.head
#                 if verb.pos_ == "VERB":
#                     if verb.tag_ in ("VB", "VBP"):  # 原形または現在形（複数形）で三単現でない
#                         print(f"⚠️ 三単現の's'の疑い: 「{line}」")
#                         print(f"   主語: '{subj.text}'（{subj.tag_}） → 動詞: '{verb.text}'（{verb.tag_}）\n")


def check_unnecessary_third_person_s(lines):
    """
    不要な三単現の's'（非三単現主語 + VBZ）の疑いをチェック（厳密な主語抽出あり）。
    """
    non_s_pronouns = {"i", "we", "you", "they"}

    for line in lines:
        doc = nlp(line)

        for chunk in doc.noun_chunks:
            if chunk.root.dep_ != "nsubj":
                continue

            subj = chunk.root
            verb = subj.head

            if verb.pos_ != "VERB" or verb.tag_ != "VBZ":
                continue  # 三単現動詞以外は対象外

            subj_text = subj.text.lower()

            # Case 1: 代名詞のパターン
            if subj.tag_ == "PRP" and subj_text in non_s_pronouns:
                print(f"⚠️ 不要な三単現の's'の疑い: 「{line}」")
                print(f"   主語: '{subj.text}'（PRP） → 動詞: '{verb.text}'（VBZ）\n")
                continue

            # Case 2: 名詞の複数形
            if subj.tag_ in ("NNS", "NNPS") or subj.morph.get("Number") == ["Plur"]:
                print(f"⚠️ 不要な三単現の's'の疑い: 「{line}」")
                print(f"   主語: '{chunk.text}'（複数形） → 動詞: '{verb.text}'（VBZ）\n")
                continue

            # Case 3: and による複数主語
            if "and" in [t.text.lower() for t in chunk if t.dep_ in ("cc", "conj")]:
                print(f"⚠️ 不要な三単現の's'の疑い（andによる複数主語）: 「{line}」")
                print(f"   主語句: '{chunk.text}' → 動詞: '{verb.text}'（VBZ）\n")
                continue

# def check_unnecessary_third_person_s(lines):
#     """
#     s が不要な主語（I, we, you, they, 複数名詞など）に対して、
#     三単現の動詞（VBZ）が使われている場合に警告を出す。
#     """
#     third_person_singular_pronouns = {"he", "she", "it"}
#     non_s_pronouns = {"i", "we", "you", "they"}

#     for line in lines:
#         doc = nlp(line)

#         for token in doc:
#             if token.dep_ != "nsubj":
#                 continue

#             verb = token.head
#             if verb.pos_ != "VERB" or verb.tag_ != "VBZ":
#                 continue

#             # case 1: 主語が代名詞（you, we, etc.）で三単現でない
#             if token.tag_ == "PRP" and token.text.lower() in non_s_pronouns:
#                 print(f"⚠️ 不要な三単現の's'の疑い: 「{line}」")
#                 print(f"   主語: '{token.text}'（{token.tag_}） → 動詞: '{verb.text}'（{verb.tag_}）\n")
#                 continue

#             # case 2: 主語が複数形の名詞
#             if token.tag_ in ("NNS", "NNPS") or token.morph.get("Number") == ["Plur"]:
#                 print(f"⚠️ 不要な三単現の's'の疑い: 「{line}」")
#                 print(f"   主語: '{token.text}'（{token.tag_}） → 動詞: '{verb.text}'（{verb.tag_}）\n")
#                 continue

#             # case 3: 主語が複数形構文（A and Bなど）
#             if "and" in [t.text.lower() for t in token.subtree]:
#                 print(f"⚠️ 不要な三単現の's'の疑い（複数主語）: 「{line}」")
#                 print(f"   主語: '{token.text}' → 動詞: '{verb.text}'（{verb.tag_}）\n")



def main():
    parser = argparse.ArgumentParser(description="Check for subject-verb agreement (3rd person singular) in LaTeX files.")
    parser.add_argument("tex_file", help="Path to the LaTeX (.tex) file")

    args = parser.parse_args()
    lines = extract_english_text_from_tex(args.tex_file)
    check_subject_verb_agreement(lines)
    check_unnecessary_third_person_s(lines)
    

if __name__ == "__main__":
    main()
                        
