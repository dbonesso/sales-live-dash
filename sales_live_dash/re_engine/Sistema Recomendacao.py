import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori
from mlxtend.frequent_patterns import fpgrowth
from mlxtend.frequent_patterns import association_rules

# Ler o CSV com o encoding para LATIN-1 por causa do dado estar trocado no Kaggle
df = pd.read_csv("data.csv", encoding='ISO-8859-1')

# Escrever os dados do CSV em um novo arquivo XLSX
df.to_excel("data.xlsx", index=False)

# Ler o arquivo xlsx gerado e armazenar em uma variável dataframe
df = pd.read_excel('data.xlsx')

# Adicionando '_' aos valores de StockCode
df['StockCode'] = df['StockCode'].apply(lambda x: '_'+str(x))

######## Quebrando o data set em 2: Um para regras de associacao
######## E outro para procurar descricoes para mostrar em nossas recomendacoes

# Criacao da variavel DataFrame para construir o sistema de recomendacoes
compras = df[['InvoiceNo', 'StockCode']]

# Criacao da variavel DataFram para devolver a descricao dos produtos
produtos = df[['StockCode', 'Description']].copy()

# Transformando todos os valores de StockCode para maiusculo - trataremos mais pra frente
produtos['StockCode'] = produtos['StockCode'].str.upper()

# Para remover valores duplicados de Produtos
produtos = produtos[~produtos.duplicated()]

# Transformar descricoes em maiusculo
produtos = produtos[
    produtos['Description'].str.upper() == produtos['Description']
]

# Manter somente uma descricao para cada Stock Code caso tenha duplicado
produtos = produtos[~produtos.duplicated(subset=['StockCode'])]

# Montar o índice para Stock Code
produtos = produtos.set_index('StockCode')
# Converter para Series para rodar as buscas de maneira mais rápida
produtos = produtos['Description']

te = TransactionEncoder()
# Uso do Fit para transformar a lista 'compras' em uma matriz binaria, sera usada logo abaixo
te_fit = te.fit(compras['StockCode'])
# Usando transform para trazer um output da matriz binaria gerada pelo fit anteriormente
compras_array = te_fit.transform(compras['StockCode'])

# Converter compras_array para um DataFrame
compras_array = pd.DataFrame(compras_array, columns =te.columns_)

def string_list(x):
    return [str(i) for i in x]

compras = compras.groupby('InvoiceNo')['StockCode'].apply(list).reset_index()
compras.head()

te = TransactionEncoder()

te.fit(compras['StockCode'])
compras_array = te.transform(compras['StockCode'])

compras_array = pd.DataFrame(compras_array, columns =te.columns_)

apriori(compras_array, min_support=0.01, max_len=2, use_colnames=True)

is_ap = apriori(compras_array, min_support=0.01, max_len=2, use_colnames=True)

fpgrowth(compras_array, min_support=0.01, max_len=2, use_colnames=True)

is_fp = fpgrowth(compras_array, min_support=0.01, max_len=2, use_colnames=True)

def itemset_to_ordered_string(itemset):
    return ','.join(sorted(list(itemset)))


ap_itemset_str = is_ap['itemsets'].apply(itemset_to_ordered_string)
ap_itemset_str = ap_itemset_str.sort_values().reset_index(drop=True)
ap_itemset_str.head()

fp_itemset_str = is_fp['itemsets'].apply(itemset_to_ordered_string)
fp_itemset_str = fp_itemset_str.sort_values().reset_index(drop=True)
fp_itemset_str.head()

# Teste para checar se ambos list set de FP e AP são iguais
fp_itemset_str.equals(ap_itemset_str)


rules = association_rules(is_fp, metric="lift", min_threshold=10)

def predict(antecedent, rules, max_results= 6):
    
    # Pegar o valor de rules para o antecedente chamado
    preds = rules[rules['antecedents'] == antecedent]
    
    # Convertendo preds coletado acima (que contem um valor) para string
    preds = preds['consequents'].apply(iter).apply(next)
    
    return preds.iloc[:max_results].reset_index(drop=True)

preds = predict({'_20712'}, rules)

# Para trazer o valor do Stock Code desse número, execute: 
# Print(produtos['_20712']) 

for stockid in preds:  
    print(produtos[stockid])