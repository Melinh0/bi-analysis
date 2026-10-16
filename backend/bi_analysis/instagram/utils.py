import re
import json
import logging
import jmespath
from datetime import datetime
import pandas as pd

from bi_analysis.logger.log import Log

_FEED_USER_PATTERN = re.compile(r'https://(?:www|i)\.instagram\.com/api/v1/feed/user/')
_MEDIA_PATTERN = re.compile(r'https://(?:www|i)\.instagram\.com/api/v1/media/')

def remover_emoji(string: str) -> str:
    

    emoji_pattern = re.compile("["
                           u"\U0001F600-\U0001F64F"
                           u"\U0001F300-\U0001F5FF"
                           u"\U0001F680-\U0001F6FF"
                           u"\U0001F1E0-\U0001F1FF"
                           u"\U00002702-\U000027B0"
                           u"\U000024C2-\U0001F251"
                           "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', string)

def sentimento(score: float) -> str:
    

    if score <= -0.2:
        return 'Negativo'
    elif score >= 0.2:
        return 'Positivo'
    else:
        return 'Neutro'
    
def taxa_emocional(magnitude: float) -> str:
    

    if magnitude < 1:
        return 'Baixa'
    elif magnitude >= 1 and magnitude <= 1.3 :
        return 'Média'
    else:
        return 'Alta'


def gerar_topicos(termos: list, model_components: list) -> dict:
    
    
    posicao = []
    topicos = []
    
    for i, comp in enumerate(model_components, start=1):

            terms_comp = zip(termos, comp)
            termos_ordenados = sorted(terms_comp, key= lambda x:x[1], reverse=True)[:15]
            palavras_chaves = []

            for t in termos_ordenados:
                 palavras_chaves.append(t[0])
    
            posicao.append(i)
            topicos.append(','.join(palavras_chaves))
    
    return {'Ordem': posicao, 'Tópico': topicos}


def sentimentalização(arquivo: str, config_file: str) -> None:
    

    try:
        from google.cloud import language_v1
        from google.oauth2 import service_account

        credenciais = service_account.Credentials.from_service_account_file(config_file)
        client = language_v1.LanguageServiceClient(credentials=credenciais)

        df = pd.read_excel(arquivo)

        
        nan_value = float("NaN")
        df.replace("", nan_value, inplace=True)
        df.dropna(subset = ["Texto"], inplace=True)

        amostra = df['Texto'].to_list()

        type_ = language_v1.Document.Type.PLAIN_TEXT
        language = "pt"
        encoding_type = language_v1.EncodingType.UTF8

        df['score'] = None
        df['magnitude'] = None

        for x in range (len(amostra)):
            
            try:
                
                document = {"content": amostra[x], "type_": type_, "language": language}
                response = client.analyze_sentiment(request = {'document': document, 'encoding_type': encoding_type})
                sentiment = response.document_sentiment

                sscore = round(sentiment.score,4)
                smag = round(sentiment.magnitude,4)
        
                df['score'][x] = sscore
                df['magnitude'][x] = smag
            
            except Exception as e:
                df['score'][x] = 0
                df['magnitude'][x] = 0
                continue

        df.dropna(subset = ["score"], inplace=True)
        df['score'].isnull().sum()

        df['Qualificação'] = df['score'].apply(sentimento)
        df['Emoção'] = df['magnitude'].apply(taxa_emocional)

        with pd.ExcelWriter(arquivo, mode='w', engine='openpyxl') as writer: 
                        df.to_excel(excel_writer=writer, sheet_name='comentários', index=False)
        
    except Exception as e:
        Log.ex('Exceção durante a execução de %s: %r', sentimentalização.__name__, e)



def remover_none(lista: list) -> list:
       while None in lista:
              lista.remove(None)
    
       return lista


def extrair_comentario(item: dict) -> dict:
        user = item.get('user') or {}
        return {
                'Usuário': user.get('username'),
                'Data': datetime.fromtimestamp(item.get('created_at')).strftime('%d-%m-%Y %H:%M:%S'),
                'Texto': item.get('text'),
                'Curtidas': item.get('comment_like_count'),
                'Respostas': item.get('child_comment_count')
        }


def extrair_post(item: dict) -> dict:
        caption = item.get('caption')
        post = {
             'Data': datetime.fromtimestamp(item.get('taken_at')).strftime('%d-%m-%Y %H:%M:%S'),
             'Curtidas': item.get('like_count'),
             'Comentários': item.get('comment_count'),
             'Texto:': caption.get('text') if isinstance(caption, dict) else None
        }
        
        url_imagem = jmespath.search("image_versions2.candidates[-1].url", item) or \
        jmespath.search("carousel_media[0].image_versions2.candidates[-1].url", item)

        post.update({'url_imagem': url_imagem})
        
        views = jmespath.search('play_count', item)
        if views is not None:
             post.update({'visualizações': views, 
                          'link': 'https://www.instagram.com/reel/' + (item.get('code') or '')})
             
             return post
        
        
        post.update({'visualizações': 0, 
                          'link': 'https://www.instagram.com/p/' + (item.get('code') or '')})
             
        return post


def obter_request_comentarios(request) -> dict:

          if _MEDIA_PATTERN.search(request.url):
                Log.i(request.url)
                return{
                         'url': request.url,
                         'headers': request.all_headers()
                    }


def obter_response_comentarios(response) -> dict:

          if _MEDIA_PATTERN.search(response.url):
                Log.i(response.url)
                return response.json()



def obter_request_feed(request) -> dict:

          url = request.url
          if _FEED_USER_PATTERN.search(url):
                  Log.i(url)
                  return{
                         'url': url,
                         'headers': request.all_headers(),
                         'tipo': 'classico',
                    }
          if 'instagram.com/graphql/query' in url:
                  try:
                        body = request.post_data or ''
                  except Exception:
                        body = ''
                  if body and ('user_id' in body or 'fetch_data' in body or 'PolarTab' in body or 'query_hash' in body):
                        Log.i(url)
                        return{
                               'url': url,
                               'headers': request.all_headers(),
                               'tipo': 'graphql',
                               'post_data': body,
                          }
          return None

def obter_response_feed(response) -> dict:

          url = response.url
          if _FEED_USER_PATTERN.search(url):
                try:
                      return response.json()
                except Exception:
                      return None
          if 'instagram.com/graphql/query' in url:
                try:
                      data = response.json()
                except Exception:
                      return None
                if _graphql_tem_feed(data):
                      return data
          return None


def _graphql_tem_feed(data) -> bool:
          if not isinstance(data, dict):
                return False
          payload = data.get('data') or {}
          if not isinstance(payload, dict):
                return False
          bloco = payload.get('xdt_api__v1__feed__user_timeline_graphql_connection')
          if isinstance(bloco, dict) and 'edges' in bloco:
                return True
          user = payload.get('user')
          if isinstance(user, dict):
                timeline = user.get('edge_owner_to_timeline_media')
                if isinstance(timeline, dict) and 'edges' in timeline:
                      return True
          return False


def normalizar_feed_graphql(data: dict) -> dict:
          payload = data.get('data') or {}
          bloco = payload.get('xdt_api__v1__feed__user_timeline_graphql_connection')
          if not isinstance(bloco, dict):
                user = payload.get('user') or {}
                bloco = user.get('edge_owner_to_timeline_media') or {}
          edges = bloco.get('edges') or []
          page_info = bloco.get('page_info') or {}
          items = []
          for edge in edges:
                node = (edge or {}).get('node')
                if not node:
                      continue
                items.append(_node_graphql_para_item(node))
          return {
                'items': items,
                'next_max_id': page_info.get('end_cursor') if page_info.get('has_next_page') else None,
          }


def _node_graphql_para_item(node: dict) -> dict:
          caption_edges = (node.get('edge_media_to_caption') or {}).get('edges') or []
          caption_text = (caption_edges[0].get('node') or {}).get('text') if caption_edges else None

          like_count = node.get('like_count') or (node.get('edge_liked_by') or {}).get('count') or 0
          comment_count = node.get('comment_count') or (node.get('edge_media_to_comment') or {}).get('count') or 0

          item = {
                'taken_at': node.get('taken_at_timestamp') or node.get('taken_at') or 0,
                'like_count': like_count,
                'comment_count': comment_count,
                'caption': {'text': caption_text} if caption_text else None,
                'code': node.get('shortcode') or node.get('code'),
                'pk': node.get('id'),
          }

          display_url = node.get('display_url') or node.get('thumbnail_src')
          if display_url:
                item['image_versions2'] = {'candidates': [{'url': display_url}]}

          if node.get('is_video'):
                item['play_count'] = node.get('video_view_count') or node.get('play_count') or 0

          return item
