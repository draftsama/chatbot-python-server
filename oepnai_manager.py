import json
import os
import openai
from openai.embeddings_utils import get_embedding, cosine_similarity
import pandas as pd
import tiktoken
import numpy as np


class openai_manager:

    # embedding method
    @staticmethod
    def create_embedding_data(source_csv_path: str, save_embedding_csv_path: str, embedding_model: str = "text-embedding-ada-002") -> pd.DataFrame:
        if os.path.exists(source_csv_path) == False:
            print("The file does not exist.")
            exit()

        raw_datas = pd.read_csv(source_csv_path, index_col=0)

        # drop any rows with missing values
        raw_datas.dropna()

        # Insert index column
        raw_datas.reset_index(inplace=True)

        # # get all columns
        # commbine_data = raw_datas.iloc[:, 0:]
        # print(commbine_data)

        # # to json object
        # json_data = json.loads(raw_datas.to_json(orient="records"))

        # create embedding data
        for i in range(0, len(raw_datas)):
            c = ""
            for attribute, value in raw_datas.iloc[i].items():
                if attribute != "embedding":
                    c += str(attribute) + ":" + str(value) + "; "

            print(c)
            # get embedding from openai api
            embedding = ""
            try:
                embedding = get_embedding(c, engine=embedding_model)
            except Exception as e:
                # ptint error message
                print(e)

            # add embedding to dataframe
            raw_datas.at[i, "embedding"] = str(embedding)
        # save to csv without index

        raw_datas.to_csv(save_embedding_csv_path, index=False)

        print(raw_datas)
        # print length
        print("Embedding data length: ", len(raw_datas.values.tolist()))
        return raw_datas

    @staticmethod
    def update_embedding_data(source_csv_path: str, embbeding_csv_path: str, embedding_model: str = "text-embedding-ada-002") -> pd.DataFrame:
        new = pd.read_csv(source_csv_path)
        current_embbeding_data = pd.read_csv(embbeding_csv_path)

        current_embbeding_data.dropna()
        new.dropna()

        # get diff between current and new data (new data - current data)
        update_datas = current_embbeding_data.merge(new, indicator=True,
                                                    how='outer', sort=True)
        diff = update_datas.loc[lambda x: x['_merge'] == 'right_only']

        diff = diff.drop(columns=["_merge"])

        update_datas = update_datas.loc[lambda x: x['_merge'] != 'left_only']
        update_datas = update_datas.drop(columns=["_merge"])

        diff = diff.drop(columns=["embedding"])

        if len(diff) == 0 and len(current_embbeding_data) == len(update_datas):

            print("No data to update")
            return current_embbeding_data

        for i in range(0, len(diff)):
            c = ""
            for attribute, value in diff.iloc[i].items():
                c += str(attribute) + ":" + str(value) + "; "

            print(c)
            index = int(diff.iloc[i].name)
            # get embedding from openai api
            embedding = "new data"
            try:
                embedding = get_embedding(c, engine=embedding_model)
            except Exception as e:
                # ptint error message
                print(e)

            update_datas.at[index, "embedding"] = str(embedding)

       # reset name of index
        update_datas.reset_index(drop=True, inplace=True)
        update_datas.to_csv(embbeding_csv_path, index=False)
        print(update_datas)
        print("Embedding data length: ", len(update_datas.values.tolist()))
        return update_datas

    # similarity method

    @staticmethod
    def get_similarity_data(prompt: str, data_embedding_path, embedding_model: str = "text-embedding-ada-002"):
        df = pd.read_csv(data_embedding_path)
        embeddings = df.embedding.apply(eval).values.tolist()
        embedding_prompt = get_embedding(prompt, engine=embedding_model)

        similarities = []
        for i, e in enumerate(embeddings):
            # add similarity score to array
            similarities.append(cosine_similarity(embedding_prompt, e))

        indexes_sort = np.argsort(similarities)[::-1]
        return indexes_sort, similarities

    @staticmethod
    def chat_completion(msg: str, training_data: str):

        # if msg is empty or training_data is empty return exception
        if msg == "" or training_data == "":
            raise Exception("msg or training_data is empty")

        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": training_data},
                {"role": "user", "content": msg},
            ]
        )

        return res.choices[0].message['content']

    @staticmethod
    def num_tokens_from_string(string: str) -> int:
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.get_encoding("cl100k_base")
        num_tokens = len(encoding.encode(string))
        return num_tokens
