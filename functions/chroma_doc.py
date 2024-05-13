import chromadb
from sentence_transformers import SentenceTransformer
from functions.embed_chrom_solution import Embed_chrom_solutionChain
from paramslist import STATUS_SQL,THRE_DIS

model = SentenceTransformer(r'/app/data/piccozh')#D:/vmware_data/docker_panzhi/docker_app/

client = chromadb.PersistentClient(path="./chromadb")  # 数据保存在磁盘

client.list_collections()

collection = client.get_or_create_collection("sql-chat")

conversation = Embed_chrom_solutionChain()

def embed_start(question):

    collection.peek()

    '''
    根据问题进行分类，得出对应的staus和action
    :param question: 用户前端输入的问题
    :return: 返回staus  action
    '''
    print("STEP1=======embedding\n")
    q_em = model.encode(question, normalize_embeddings=True)
    q_em = q_em.tolist()
    results = collection.query(
        query_embeddings=q_em,
        n_results=1,
    )
    print('\n向量数据库比对问题\n',results)
    data_res = results['documents'][0][0]
    distance = results['distances'][0][0]
    id_doc = results['ids'][0][0]
    if distance < THRE_DIS:
        print('emb-res={}'.format(data_res))
        try:
            sta = data_res.split('+')[0]
            status = sta.split(':')[-1]
            actions = data_res.split('+')[-1]
            # status = int(status)
            print("STEP1======embed==result:\n", status, actions,"\nstatus类型",type(status))
            if status in STATUS_SQL:
                if len(status) >1 and status[0] == status[1]:
                    status = status[0]
                actions = conversation.predict(status+'key:'+question+actions).content.strip()
                print('\n  大模型提取关键信息action \n',actions)
            return int(status),actions,id_doc
        except:
            return -1,data_res,id_doc

    else:
        return -1, data_res,id_doc


# while True:
#     question_input = input('请输入问题：')
#     print(embed_start(question_input))
    # q_em = model.encode(question_input,normalize_embeddings=True)
    # q_em = q_em.tolist()
    # results = collection.query(
    #     query_embeddings=q_em,
    #     n_results=1,
    # )

    # print(results)
    # print(results['documents'][0][0])
#
