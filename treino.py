import os
import pickle

import cv2
import dlib
import numpy as np


class Treinar:
    ##Função para carregar todos os arquivos com os seus devidos recursos.
    def __init__(self):
        print('[+] Carregando todos os arquivos')
        print(os.path.dirname(os.path.abspath(__file__)))
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.Sources = os.path.join(base_dir, 'recursos')
        self.Media_root = os.path.join(base_dir, 'app', 'static', 'img', 'users')
        
        #HOG
        self.detectordeFace = dlib.get_frontal_face_detector()
        ### Arquivo já treinado com os 68 pontos faciais uso de HOG E SVM ###
        self.detectordePontos = dlib.shape_predictor(self.Sources + "\\shape_predictor_68_face_landmarks.dat")
        ### Arquivo que já é um .dat treinado especificamente para fazer reconhecimento facial, onde ele está utilizando a rede neural convulucional (Contém os descritores da face) ###
        self.reconhecimentoFacial = dlib.face_recognition_model_v1(self.Sources + "\\dlib_face_recognition_resnet_model_v1.dat")

        print('[-] Iniciando.')
    
    ##Função que realiza o treinamento em si.
    def run(self):
        print('[+] Treinando...')

        #
        indice = {}
        idx = 0
        descritoresFaciais = None
        ## Variável para listar os arquivos buscados anteriormente##
        categories = [dir for dir in os.listdir(self.Media_root) if os.path.isdir(os.path.join(self.Media_root, dir))]

        ## For para percorrer todas as imagens de treinamento.
        for category in categories:

            #Caminho onde fica a pasta users
            entire_path = os.path.join(self.Media_root, category)
            print('--' + entire_path)

            #For para percorrer dentro da pasta dos usuários;
            for img_path in os.listdir(entire_path):
                
                #Variável que faz a leitura de cada imagem.
                imagem = cv2.imread(os.path.join(entire_path, img_path))

                #Variável para detectar as faces das imagens, armazendando os bounding boxes de cada uma das faces que foram encontradas.
                facesDetectadas = self.detectordeFace(imagem, 1)

                #Saber quantas faces ele está detectando em cada imagem.
                numerodeFacesDetectadas = len(facesDetectadas)
                print("O número de faces é: {}, da imagem: {}".format(numerodeFacesDetectadas, img_path))

                #Se o numero de faces for diferente de 1, ele pausa e pula para o proximo usuário.
                if numerodeFacesDetectadas != 1:
                    print("Contém mais de uma imagem ou não contém nenhuma na foto {}".format(img_path))
                
                    
                
                for face in facesDetectadas:
                    # Extração dos pontos faciais de cada imagem
                    pontosFaciais = self.detectordePontos(imagem, face)
                    #Criamos um descritor facial, ele vai descrever uma face, computando quais são as principais caracteristicas que existem nessa face
                    descritorFacial = self.reconhecimentoFacial.compute_face_descriptor(imagem, pontosFaciais)
                    # print(format(img_path))
                    # print(len(descritorFacial))
                    # print(descritorFacial)

                    #Convertar os descritores de face no formato do dlib para uma lista com um tamanho 128
                    listaDescritorFacial = [df for df in descritorFacial]
                    print(listaDescritorFacial)
                    #Converte a lista em um vetor tipo numpy
                    npArrayDescritorFacial = np.asarray(listaDescritorFacial, dtype=np.float64)
                    # print(npArrayDescritorFacial)
                    npArrayDescritorFacial = npArrayDescritorFacial[np.newaxis, :]

                    #Faz uma concatenação entre os descritoes faciais e o array dos descritores faciais
                    if descritoresFaciais is None:
                        descritoresFaciais = npArrayDescritorFacial
                    else:
                        descritoresFaciais = np.concatenate((descritoresFaciais, npArrayDescritorFacial), axis=0)


                    indice[idx] = category
                    idx += 1

        print("tamanho: {} Formato: {}".format(len(descritoresFaciais), descritoresFaciais.shape))
        #Salva a concatenação dos descritores.
        np.save(self.Sources + "\\descritores_atualizado.npy", descritoresFaciais)
        #Grava os indices que são as posições com os id dos usuários.
        pickle_out = open(self.Sources + "\\indice_categories.pickle", 'wb')
        pickle.dump(indice, pickle_out)
        pickle_out.close()

        print('[-] Pronto.')

if __name__ == "__main__":
    t = Treinar()
    t.run()