import os
from copy import deepcopy
from datetime import date, datetime, timedelta

import cv2
import dlib
import numpy as np
from flask import Response, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from treino import Treinar
from werkzeug.security import check_password_hash, generate_password_hash
from wtforms import SelectField

from app import db
from app.models import Cargo, ControleEntrada, Usuario

#generate_password_hash - Gerar um hash da senha.
#check_password_hash - Compara a senha digitada pelo usuário com a senha do banco de dados(comparador de hash).

#Busca os arquivos referente ao projeto
base_dir = os.path.dirname(os.path.abspath(__file__))
#Especifica o caminho do BD
database_path = os.path.join(base_dir, 'app.db')

#Vai detectar as faces.
detectorFace = dlib.get_frontal_face_detector()
#Arquivo já treinado com os 68 pontos faciais uso de HOG E SVM
detectorPontos = dlib.shape_predictor("recursos/shape_predictor_68_face_landmarks.dat")
#Reconhecimento facial (Baseado em DLIB).
reconhecimentoFacial = dlib.face_recognition_model_v1("recursos/dlib_face_recognition_resnet_model_v1.dat")
#Listagem das imagens.
indices = np.load("recursos/indice_categories.pickle", allow_pickle=True)
#São as faces, pontos da faces.
descritoresFaciais = np.load("recursos/descritores_atualizado.npy")

#Precisão (Referente ao reconhecimento)
limiar = 0.5    
totalFaces = 0
totalAcerto = 0

#Acessar o banco de dados, e por meio de um session utilizá-lo (dentro do generate)
engine = create_engine(f'sqlite:///{database_path}')
Base = automap_base()
Base.prepare(engine, reflect=True)
#Pegar WebCam local
video = cv2.VideoCapture(0)

#Rota = é o caminho para o usuário acessar alguma função, ex: reconhecimento facial

#Inicia a aplicação em si.
def init_app(app):
    @app.route("/")
    def index():        
        return render_template("index.html")  

    #ESTÁ ROTA FOI CRIADA POIS O USUÁRIO ESCOLHE A ROTINA QUE QUER IR.
    @app.route("/rotinas")       
    def rotinas():
        return render_template("rotinas.html")

    @app.route("/usuario/<int:id>")
    #SOMENTE OS USUÁRIOS LOGADOS PODEM TER ACESSO
    @login_required
    def unique(id):
        #MOSTRA SOMENTE O USUÁRIO SELECIONADO
        usuario = Usuario.query.get(id)
        return render_template("user.html", usuario=usuario)

    @app.route("/usuarios")
    def usuarios():
        #MOSTRA TODOS USUÁRIOS
        usuarios = Usuario.query.all()
        return render_template("users.html", usuarios=usuarios)

    @app.route("/cargos")
    def cargos():
        #MOSTRA TODOS CARGOS
        cargos = Cargo.query.all()
        return render_template("cargos.html", cargos=cargos)

    @app.route("/historicos")
    def historicos():
        #MOSTRA TODOS HISTORICOS
        historicos = ControleEntrada.query.all()
        return render_template("historico.html", historicos=historicos)

    @app.route("/historico/<int:id>")
    #SOMENTE OS USUÁRIOS LOGADOS PODEM TER ACESSO
    @login_required
    def historico(id):
        #MOSTRA SOMENTE O HISTÓRICO DO USUÁRIO SELECIONADO
        historico = ControleEntrada.query.filter_by(usuario_id = id).all()
        return render_template("historicoindividual.html", historico=historico)                

    @app.route("/usuario/delete/<int:id>")
    def delete(id):
        #PEGA O PRIMEIRO USUÁRIO COM ID REFERENTE.
        usuario = Usuario.query.filter_by(id=id).first()
        #COLOCA NA SESSÃO DE DELETAR O USUÁRIO.
        db.session.delete(usuario)
        #ESCREVE NO BANCO DE DADOS.
        db.session.commit()

        #Busca os arquivos referente ao projeto
        Base_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        #Caminho da pasta do usuário
        image_path = os.path.join(Base_DIR, 'app', 'static', 'img', 'users', str(usuario.id))
        #Verifica se existe a pasta do usuário referente
        if os.path.exists(image_path):
            #Listar tudo que existe na pasta
            dir = os.listdir(image_path)
            #Loop enquanto houver arquivos dentro da pasta
            for file in dir:
                #Se existir arquivo png deleta img
                if file.endswith('.png'):
                    os.remove(os.path.join(image_path, file))
            os.rmdir(image_path)

        #Realiza o treinamento
        t = Treinar()
        t.run()
        #REDIRECIONA PARA "/"
        return redirect("/usuarios")

    @app.route("/cargo/delete/<int:id>")
    def deletecargo(id):
        #PEGA O PRIMEIRO CARGO COM ID REFERENTE.
        cargo = Cargo.query.filter_by(id=id).first()
        #COLOCA NA SESSÃO DE DELETAR O CARGO.
        db.session.delete(cargo)
        #ESCREVE NO BANCO DE DADOS.
        db.session.commit()

        #REDIRECIONA PARA "/"
        return redirect(url_for("cargos"))

    @app.route("/registro", methods=["GET", "POST"])
    def registro():
        form = Form()
        #MONTA SELECT DE CARGOS
        form.cargos.choices = [(cargo.id, cargo.descricao) for cargo in Cargo.query.all()]
        
        #VERIFICANDO SE A REQUISIÇÃO É VIA POST
        if request.method == "POST":
            usuario = Usuario()
            usuario.nome = request.form["nome"]
            usuario.cpf = request.form["cpf"]
            usuario.datanascimento = datetime.strptime(request.form["datanascimento"], "%d/%m/%Y").date()
            usuario.email = request.form["email"]
            usuario.cargo_id = request.form["cargos"]
            usuario.senha = generate_password_hash(request.form["senha"])

            #COLOCA NA SESSÃO DE SALVAR UM USUÁRIO.
            db.session.add(usuario)
            #ESCREVE NO BANCO DE DADOS.
            db.session.commit()

            return redirect(url_for("usuarios"))

        return render_template("registro.html", form=form)

    @app.route("/novousuario", methods=["GET", "POST"])
    def novousuario():
        form = Form()
        #MONTA SELECT DE CARGOS
        form.cargos.choices = [(cargo.id, cargo.descricao) for cargo in Cargo.query.all()]
        
        #VERIFICANDO SE A REQUISIÇÃO É VIA POST
        if request.method == "POST":
            usuario = Usuario()
            usuario.nome = request.form["nome"]
            usuario.cpf = request.form["cpf"]
            usuario.datanascimento = datetime.strptime(request.form["datanascimento"], "%d/%m/%Y").date()
            usuario.email = request.form["email"]            
            usuario.senha = generate_password_hash(request.form["senha"])

            #COLOCA NA SESSÃO DE SALVAR UM USUÁRIO.
            db.session.add(usuario)
            #ESCREVE NO BANCO DE DADOS.
            db.session.commit()

            return redirect(url_for("login"))

        return render_template("registro.html", form=form)

    @app.route("/registrocargos", methods=["GET", "POST"])
    def registrocargos():
        #VERIFICANDO SE A REQUISIÇÃO É VIA POST
        if request.method == "POST":
            cargo = Cargo()
            cargo.descricao = request.form["descricao"]
            cargo.salario = request.form["salario"]

            #COLOCA NA SESSÃO DE SALVAR UM USUÁRIO.
            db.session.add(cargo)
            #ESCREVE NO BANCO DE DADOS.
            db.session.commit()

            return redirect(url_for("cargos"))

        return render_template("registrocargos.html")

    #CADASTRO DAS FACES DOS USUÁRIOS
    @app.route("/cadastrarfotos/<int:id>", methods=["GET", "POST"])
    def cadastrarfotos(id):
        return render_template("cadastrarfotos.html", id=id)

    #Realiza o treinamento
    @app.route("/treinar_usuarios")
    def treinar_usuarios():
        t = Treinar()
        t.run()

        usuarios = Usuario.query.all()
        return render_template("users.html", usuarios=usuarios)

    #Realiza o Controle de Ponto
    @app.route("/controle_acesso", methods=["GET", "POST"])
    def controle_acesso():
        return render_template("controledeacesso.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        #VERIFICANDO SE A REQUISIÇÃO É VIA POST
        if request.method == "POST":
            email = request.form["email"]
            senha = request.form["senha"]

            #VERIFICA SE ESSE USUÁRIO EXISTE, E PEGANDO A PRIMEIRO OCORRÊNCIA
            usuario = Usuario.query.filter_by(email=email).first()

            #SE NÃO EXISTIR, VOLTA PARA TELA DE LOGIN
            if not usuario:
                flash("Credênciais inválidas.")
                return redirect(url_for("login"))

            #VERIFICA SE A SENHA ESTÁ CERTA
            if not check_password_hash(usuario.senha, senha):
                flash("Credênciais inválidas.")
                return redirect(url_for("login"))

            login_user(usuario)
            return redirect(url_for("rotinas"))

        return render_template("login.html")

    #Deslogar o usuário que está logado
    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("index"))

    class Form(FlaskForm):
        #CLASSE PARA GERAR A SELECT DE CARGOS
        cargos = SelectField('cargos', choices=[])

    #Essa rota passa o vídeo stremado com o reconhecimento facial
    @app.route('/video_reconhecimento') 
    def video_reconhecimento():
        global video

        foto = reconhecimento(video, Usuario, ControleEntrada)

        return Response(foto, mimetype='multipart/x-mixed-replace; boundary=frame')

    #Contém o reconhecimento facial
    def reconhecimento(video_reconhecimento, Usuario, ControleEntrada):
        #Banco de dados
        session = Session(engine)
        #Indices das imagens treinadas
        indices = np.load("recursos/indice_categories.pickle", allow_pickle=True)
        #Descritores das imagens treinadas
        descritoresFaciais = np.load("recursos/descritores_atualizado.npy")

        ultimoUsuarioSalvo = 0   
        date_1 = datetime.now()

        while True:
            #Verifica se a WebCam está conectada
            conectado, imagem = video_reconhecimento.read()
            #Transforma o frame em cinza
            frame_cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
            ##Cria os bounding boxes e com o paramêtro 1 pois temos imagens grandes, se as imagens fossem menores o parametro seria 2. 
            facesDetectadas = detectorFace(imagem, 1)

            ##Percorrimento das faces detectadas, irá percorrer em cada um bounding boxes das faces detectadas.
            for face in facesDetectadas:
                ##Extração dos pontos de e= esquerda, t= topo, d= direita e b= baixo.
                e, t, d, b = (int(face.left()), int(face.top()), int(face.right()), int(face.bottom()))
                ##Pega a imagem em cinza e verifica todos os 68 pontos, enviando os pontos para o nosso classificador a rede neural.
                pontosFaciais = detectorPontos(frame_cinza, face)
                ##Descritor de face com reconhecimento facial e com os pontos faciais, com um conjutno de 128 caracteristicas da aplicação das convuluções, encontrando as melhores caracteristicas dessa imagem.
                descritorFacial = reconhecimentoFacial.compute_face_descriptor(imagem, pontosFaciais)
                print(len(descritorFacial))
                ##Converte o descritor facial em formato de lista.
                listaDescritorFacial = [fd for fd in descritorFacial]
                ##Converter a lista para um array tipo numpy.
                npArrayDescritorFacial = np.asarray(listaDescritorFacial, dtype=np.float64)
                ##Adiciona mais uma coluna nele.
                npArrayDescritorFacial = npArrayDescritorFacial[np.newaxis, :]
                print("Array dos 128 descritores:",npArrayDescritorFacial)

                ##Aplicação do KNN, o linalg faz o calculo da distancia euclidiana, o norm faz a normalização dos dados, o axis=1 pega os valores da coluna 1.
                distancias = np.linalg.norm(npArrayDescritorFacial - descritoresFaciais, axis=1)
                print("Distancia:{}".format(distancias))
                ##Vai mostrar a posição do menor distancia.
                minimo = np.argmin(distancias)
                print('A posição do menor distância é:', minimo)
                ##Vai mostra qual é a menor distância.
                distanciaMinima = distancias[minimo]
                print('A menor distância é:', distanciaMinima)

                #Limiar => é a variável de precisão (Sempre que o número for menor a precisão é maior)
                if distanciaMinima <= limiar:

                    ##Id do usuário nas pastas.
                    id_ = os.path.split(indices[minimo])[1].split(".")[0]
                    ##Pegando o usuário do banco de dados.
                    usuario = session.query(Usuario).filter_by(id=id_).first()
                    
                    ##Calculo da porcentagem
                    dist = (str(1.0 - distanciaMinima).split('.')[1])[:2]
                    ##faz o desenho do retângulo na face da pessoa.
                    cv2.rectangle(imagem, (e, t), (d, b), (0, 255, 0), 2)
                    ##variável texto onde traz a dist= porcentagem e usuario.nome= nome do usuário.
                    texto = f'{dist}% {usuario.nome}'

                    ##Coloca um texto na imagem com a variável texto.
                    cv2.putText(imagem, texto, (e, t), cv2.FONT_ITALIC, 0.4, (0, 0, 255))  

                    dataHoraAtual = datetime.now()
                    dataHoraAtual.strftime('%d/%m/%Y %H:%M')

                    dataAtual = date.today()

                    date_2 = datetime.now()
                    time_delta = (date_2 - date_1)
                    total_seconds = time_delta.total_seconds()
                    minutes = total_seconds/60
                    # print('Minutos final: ', minutes)

                    #Quando a diferença de horas/minutos atingir 5 minutos do primeiro acesso, realiza um novo registro
                    if minutes > 5:
                        ultimoUsuarioSalvo = 0
                        date_1 = datetime.now()

                    if int(dist) > 55 and ultimoUsuarioSalvo != int(id_): 
                        controle = ControleEntrada()
                        controle.usuario_id = int(id_)

                        #Pega o ultimo registro do controle de acesso.
                        controleteste = session.query(ControleEntrada).filter_by(usuario_id=id_).order_by(ControleEntrada.id.desc()).first()
                        
                        #Se for diferente de null pega a data de entrada
                        if controleteste!=None:
                            dataentrada = controleteste.datahora_acesso_entrada

                            #Se a data de entrada for igual ao dia atual e maior que o horario de entrada, faz o update na data saida
                            if dataentrada.strftime('%Y-%m-%d') == dataAtual.strftime('%Y-%m-%d'):
                                if dataHoraAtual.hour > 13:
                                    admin = session.query(ControleEntrada).filter_by(id=controleteste.id).first()
                                    admin.datahora_acesso_saida = dataHoraAtual

                            #Se a data nao for igual e o horario de entrada for menor que 13 ele grava uma entrada                                    
                            elif dataHoraAtual.hour <= 13:
                                controle.datahora_acesso_entrada = dataHoraAtual
                                session.add(controle)

                        #Se nao houver entrada, ele grava entrada
                        elif dataHoraAtual.hour <= 13:
                            controle.datahora_acesso_entrada = dataHoraAtual
                            session.add(controle)

                        session.commit()

                        ultimoUsuarioSalvo = int(id_)

            ret, jpeg = cv2.imencode('.jpg', imagem)

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')

    #Rota do vídeo Cru
    @app.route('/video')                
    def video():
        global video
        return Response(video_cru(video), mimetype='multipart/x-mixed-replace; boundary=frame')

    #Vídeo streaming cru
    def video_cru(video):               
        while True:
            conectado, imagem = video.read()
            ret, jpeg = cv2.imencode('.jpg', imagem)
            
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')

    #Botão de screen shot da tela.
    def botao_print(video, path):       
        Base_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        image_path = os.path.join(Base_DIR, 'app', 'static', 'img', 'users', str(path))
        
        if not os.path.exists(image_path):
            
            os.mkdir(image_path)

        img_count = len(os.listdir(image_path)) + 1

        open, image = video.read()
        cv2.imwrite(os.path.join(image_path, 'imagem_' + str(img_count) + '.png'), image)

    #Rota do print
    @app.route('/print_/<int:id>')
    def print_(id):
        global video
        botao_print(video, path=id)
        return render_template("cadastrarfotos.html", id=id)