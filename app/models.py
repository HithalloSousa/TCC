from flask_login import UserMixin

from app import db, login_manager

#UserMixin - interface que importa todas as classes necessários do usuario.

#SEMPRE TRAZER O USUÁRIO QUE ESTÁ LOGADO.
@login_manager.user_loader                                                 
def current_user(usuario_id):
    return Usuario.query.get(usuario_id)

#HERANÇA DE UMA OUTRA CLASSE(ORIENTAÇÃO A OBJETO APLICADO NO PYTHON).
class Usuario(db.Model, UserMixin):                                        
    #NOME DA TABELA E SEUS CAMPOS.
    __tablename__ = "usuarios"                                             
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(84), nullable=False)
    cpf = db.Column(db.String(84), nullable=False)
    datanascimento = db.Column(db.Date, nullable=False)
    #SÓ ACEITA UM E-MAIL.
    email = db.Column(db.String(84), nullable=False, unique=True, index=True)   
    senha = db.Column(db.String(255), nullable=False)

    #RELACIONAMENTO COM A TABELA DE CARGOS.
    cargo_id = db.Column(db.Integer, db.ForeignKey('cargos.id'))                
    #1 CARGO PODE ESTAR EM VARIOS USUÁRIOS.
    cargo = db.relationship("Cargo")                                            

    #1 USUÁRIO PODE CONTER 1 OU MAIS PONTO.
    ponto = db.relationship("ControleEntrada")                                  

    def __str__(self):
        return self.nome

class Cargo(db.Model):
    __tablename__ = "cargos"
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(255), nullable=False)
    salario = db.Column(db.Float)

    def __str__(self):
        return self.id    

class ControleEntrada(db.Model):
    __tablename__ = "controleponto"
    id = db.Column(db.Integer, primary_key=True)    
    datahora_acesso_entrada = db.Column(db.DateTime)
    datahora_acesso_saida = db.Column(db.DateTime)
    #FK COM A USUARIOS
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    usario = db.relationship("Usuario")

    def __str__(self):
        return self.id