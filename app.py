from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///denuncias.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

AREAS_PADRAO = [
    'Tecnologia','Jurídico','Saúde','Educação','Administrativo','Marketing',
    'Vendas','Financeiro','Recursos Humanos','Engenharia','Design','Comunicação','Outros'
]

usuario_logado_id = None
denuncia_atual_id = None


class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    login = db.Column(db.String(50), nullable=False)
    senha = db.Column(db.String(100), nullable=False)
    area = db.Column(db.String(50))
    tipo = db.Column(db.String(20))  

class Denuncia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200))
    descricao = db.Column(db.Text)
    tipo = db.Column(db.String(50))  
    empresa = db.Column(db.String(200))
    area_trabalho = db.Column(db.String(50))
    anonima = db.Column(db.Boolean, default=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    cidade = db.Column(db.String(100))
    area_usuario = db.Column(db.String(50))
    apoios = db.Column(db.Integer, default=0)

class Apoio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer)
    denuncia_id = db.Column(db.Integer)

class Comentario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.Text)
    denuncia_id = db.Column(db.Integer)
    usuario_id = db.Column(db.Integer)
    fixado = db.Column(db.Boolean, default=False)
    tipo_usuario = db.Column(db.String(20))
    anonimo = db.Column(db.Boolean, default=False)


def ranking_empresas():
    denuncias_todas = Denuncia.query.all()
    contagem = {}
    for d in denuncias_todas:
        empresa = d.empresa or 'Não informada'
        contagem[empresa] = contagem.get(empresa, 0) + 1

    lista_empresas = [[emp, qtd] for emp, qtd in contagem.items()]
    lista_empresas.sort(key=lambda x: x[1], reverse=True)
    return lista_empresas[:10]

def usuario_atual_obj():
    global usuario_logado_id
    if usuario_logado_id:
        return Usuario.query.get(usuario_logado_id)
    return None


@app.route('/')
def home():
    usuario = usuario_atual_obj()
    todas_denuncias = Denuncia.query.all()
    ranking = ranking_empresas()

    total_denuncias = len(todas_denuncias)
    contagem_moral = sum(1 for d in todas_denuncias if d.tipo == 'moral')
    contagem_sexual = sum(1 for d in todas_denuncias if d.tipo == 'sexual')
    contagem_salarial = sum(1 for d in todas_denuncias if d.tipo == 'salarial')

    return render_template('index.html',
                           denuncias=todas_denuncias,
                           usuario=usuario,
                           ranking=ranking,
                           total_denuncias=total_denuncias,
                           contagem_moral=contagem_moral,
                           contagem_sexual=contagem_sexual,
                           contagem_salarial=contagem_salarial,
                           areas=AREAS_PADRAO,
                           filtro_area='',
                           filtro_cidade='',
                           todos_usuarios=Usuario.query.all())


@app.route('/login', methods=['GET', 'POST'])
def login():
    global usuario_logado_id
    if request.method == 'POST':
        login_input = request.form.get('login')
        senha = request.form.get('senha')

        if not login_input or not senha:
            return render_template('login.html', erro='Preencha login e senha')

        usuario = Usuario.query.filter_by(login=login_input, senha=senha).first()
        if usuario:
            usuario_logado_id = usuario.id
            return redirect('/')
        else:
            return render_template('login.html', erro='Login ou senha incorretos')
    return render_template('login.html')

@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    global usuario_logado_id
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        login_field = request.form.get('login', '').strip()
        senha = request.form.get('senha', '').strip()
        area = request.form.get('area', '')
        tipo = request.form.get('tipo', 'comum')

        if len(nome) < 2:
            return render_template('cadastrar.html', erro='Nome muito curto!', areas=AREAS_PADRAO)
        if '@' not in email:
            return render_template('cadastrar.html', erro='Email inválido!', areas=AREAS_PADRAO)
        if len(senha) < 4:
            return render_template('cadastrar.html', erro='Senha muito curta!', areas=AREAS_PADRAO)
        if not login_field:
            return render_template('cadastrar.html', erro='Informe um login!', areas=AREAS_PADRAO)

        existente_email = Usuario.query.filter_by(email=email).first()
        if existente_email:
            return render_template('cadastrar.html', erro='Email já cadastrado!', areas=AREAS_PADRAO)
        existente_login = Usuario.query.filter_by(login=login_field).first()
        if existente_login:
            return render_template('cadastrar.html', erro='Login já usado!', areas=AREAS_PADRAO)

        novo = Usuario(nome=nome, email=email, login=login_field, senha=senha, area=area, tipo=tipo)
        db.session.add(novo)
        db.session.commit()

        usuario_logado_id = novo.id
        return redirect('/')

    return render_template('cadastrar.html', areas=AREAS_PADRAO)

@app.route('/logout')
def logout():
    global usuario_logado_id
    usuario_logado_id = None
    return redirect('/')


@app.route('/denunciar')
def denunciar():
    usuario = usuario_atual_obj()
    if not usuario:
        return redirect('/login')
    if usuario.tipo != 'vitima' and usuario.tipo != 'comum':
        return redirect('/')
    return render_template('denunciar.html', areas=AREAS_PADRAO)

@app.route('/nova_denuncia', methods=['POST'])
def nova_denuncia():
    usuario = usuario_atual_obj()
    if not usuario:
        return redirect('/login')
    titulo = request.form.get('titulo')
    descricao = request.form.get('descricao')
    tipo = request.form.get('tipo')
    empresa = request.form.get('empresa') or 'Não informada'
    area_trabalho = request.form.get('area_trabalho') or usuario.area
    cidade = request.form.get('cidade') or ''
    anonima = 'anonima' in request.form

    if not titulo or not descricao:
        return render_template('denunciar.html', erro='Preencha todos os campos', areas=AREAS_PADRAO)

    nova = Denuncia(
        titulo=titulo,
        descricao=descricao,
        tipo=tipo,
        empresa=empresa,
        area_trabalho=area_trabalho,
        anonima=anonima,
        usuario_id=usuario.id,
        cidade=cidade.title(),
        area_usuario=usuario.area,
        apoios=0
    )
    db.session.add(nova)
    db.session.commit()
    return redirect('/')

@app.route('/selecionar_denuncia', methods=['POST'])
def selecionar_denuncia():
    global denuncia_atual_id
    try:
        denuncia_atual_id = int(request.form.get('denuncia_id'))
    except (TypeError, ValueError):
        denuncia_atual_id = None
    return redirect('/ver_denuncia')

@app.route('/ver_denuncia')
def ver_denuncia():
    global denuncia_atual_id
    if not denuncia_atual_id:
        return redirect('/')
    denuncia = Denuncia.query.get(denuncia_atual_id)
    if not denuncia:
        return redirect('/')
    usuario = usuario_atual_obj()
    apoiou = False
    empresa_correta = False

    if usuario:
        apoio = Apoio.query.filter_by(usuario_id=usuario.id, denuncia_id=denuncia.id).first()
        apoiou = True if apoio else False
        empresa_correta = (usuario.tipo == 'empresa' and usuario.nome == denuncia.empresa)

    comentarios = Comentario.query.filter_by(denuncia_id=denuncia.id).all()
    return render_template('denuncia.html',
                           denuncia=denuncia,
                           usuario=usuario,
                           comentarios=comentarios,
                           ja_apoiou=apoiou,
                           empresa_da_denuncia=empresa_correta)

# comentar
@app.route('/comentar', methods=['POST'])
def comentar():
    global denuncia_atual_id
    if not usuario_logado_id or not denuncia_atual_id:
        return redirect('/login')
    usuario = Usuario.query.get(usuario_logado_id)
    denuncia = Denuncia.query.get(denuncia_atual_id)
    if not usuario or not denuncia:
        return redirect('/')

    if usuario.tipo == 'empresa' and usuario.nome != denuncia.empresa:
        return redirect('/ver_denuncia')

    texto = request.form.get('texto', '').strip()
    if not texto:
        return redirect('/ver_denuncia')

    anonimo = 'anonimo' in request.form
    fixar = (usuario.tipo == 'empresa')

    comentario = Comentario(
        texto=texto,
        denuncia_id=denuncia.id,
        usuario_id=usuario.id,
        tipo_usuario=usuario.tipo,
        fixado=fixar,
        anonimo=anonimo
    )
    db.session.add(comentario)
    db.session.commit()
    return redirect('/ver_denuncia')

@app.route('/apoio')
def apoio():
    global denuncia_atual_id
    if not usuario_logado_id or not denuncia_atual_id:
        return redirect('/login')
    usuario = Usuario.query.get(usuario_logado_id)
    denuncia = Denuncia.query.get(denuncia_atual_id)
    if not usuario or not denuncia:
        return redirect('/')

    if usuario.tipo == 'empresa':
        return redirect('/ver_denuncia')

    apoio_antigo = Apoio.query.filter_by(usuario_id=usuario.id, denuncia_id=denuncia.id).first()
    if apoio_antigo:
        db.session.delete(apoio_antigo)
        if denuncia.apoios and denuncia.apoios > 0:
            denuncia.apoios -= 1
    else:
        apoio_novo = Apoio(usuario_id=usuario.id, denuncia_id=denuncia.id)
        db.session.add(apoio_novo)
        denuncia.apoios = (denuncia.apoios or 0) + 1

    db.session.commit()
    return redirect('/ver_denuncia')


@app.route('/perfil')
def perfil():
    usuario = usuario_atual_obj()
    if not usuario:
        return redirect('/login')
    if usuario.tipo == 'vitima' or usuario.tipo == 'comum':
        denuncias = Denuncia.query.filter_by(usuario_id=usuario.id).all()
    else:
        denuncias = Denuncia.query.filter_by(empresa=usuario.nome).all()
    return render_template('perfil.html', usuario=usuario, denuncias=denuncias)

@app.route('/selecionar_editar', methods=['POST'])
def selecionar_editar():
    global denuncia_atual_id
    try:
        denuncia_atual_id = int(request.form.get('denuncia_id'))
    except (TypeError, ValueError):
        denuncia_atual_id = None
    return redirect('/editar')

@app.route('/editar', methods=['GET', 'POST'])
def editar():
    global denuncia_atual_id
    if not usuario_logado_id or not denuncia_atual_id:
        return redirect('/login')
    usuario = Usuario.query.get(usuario_logado_id)
    denuncia = Denuncia.query.get(denuncia_atual_id)
    if not usuario or not denuncia:
        return redirect('/perfil')

    if denuncia.usuario_id != usuario.id:
        return redirect('/perfil')

    if request.method == 'POST':
        denuncia.titulo = request.form.get('titulo')
        denuncia.descricao = request.form.get('descricao')
        denuncia.tipo = request.form.get('tipo')
        denuncia.empresa = request.form.get('empresa')
        denuncia.area_trabalho = request.form.get('area_trabalho')
        denuncia.cidade = (request.form.get('cidade') or '').title()
        denuncia.anonima = 'anonima' in request.form
        db.session.commit()
        return redirect('/perfil')

    return render_template('editar.html', denuncia=denuncia, areas=AREAS_PADRAO)

@app.route('/deletar')
def deletar():
    usuario = usuario_atual_obj()
    if not usuario:
        return redirect('/login')

    id_para_remover = request.args.get('id')
    if not id_para_remover:
        return redirect('/perfil')

    try:
        id_int = int(id_para_remover)
    except ValueError:
        return redirect('/perfil')

    denuncia = Denuncia.query.get(id_int)
    if denuncia and denuncia.usuario_id == usuario.id:
        apoios = Apoio.query.filter_by(denuncia_id=id_int).all()
        for apoio_obj in apoios:
            db.session.delete(apoio_obj)
        comentarios = Comentario.query.filter_by(denuncia_id=id_int).all()
        for comm in comentarios:
            db.session.delete(comm)
        db.session.delete(denuncia)
        db.session.commit()
    return redirect('/perfil')


@app.route('/minhas_denuncias')
def minhas_denuncias():
    usuario = usuario_atual_obj()
    if not usuario:
        return redirect('/login')
    denuncias = Denuncia.query.filter_by(usuario_id=usuario.id).all()
    return render_template('minhas_denuncias.html', usuario=usuario, denuncias=denuncias)

@app.route('/area/<area_nome>')
def filtrar_por_area(area_nome):
    denuncias = Denuncia.query.filter_by(area_usuario=area_nome).all()
    total_denuncias = len(denuncias)
    contagem_moral = sum(1 for d in denuncias if d.tipo == "moral")
    contagem_sexual = sum(1 for d in denuncias if d.tipo == "sexual")
    contagem_salarial = sum(1 for d in denuncias if d.tipo == "salarial")
    usuario = usuario_atual_obj()
    return render_template('index.html',
                           denuncias=denuncias,
                           total_denuncias=total_denuncias,
                           contagem_moral=contagem_moral,
                           contagem_sexual=contagem_sexual,
                           contagem_salarial=contagem_salarial,
                           usuario=usuario,
                           areas=AREAS_PADRAO,
                           filtro_area=area_nome,
                           filtro_cidade='',
                           ranking=ranking_empresas(),
                           todos_usuarios=Usuario.query.all())

@app.route('/filtrar_localizacao')
def filtrar_localizacao():
    cidade = request.args.get("cidade")
    if not cidade:
        return redirect("/")
    cidade = cidade.title()
    denuncias_filtradas = Denuncia.query.filter_by(cidade=cidade).all()
    usuario = usuario_atual_obj()
    total = len(denuncias_filtradas)
    return render_template(
        "index.html",
        denuncias=denuncias_filtradas,
        filtro_cidade=cidade,
        filtro_area='',
        total_denuncias=total,
        contagem_moral=sum(1 for d in denuncias_filtradas if d.tipo == "moral"),
        contagem_sexual=sum(1 for d in denuncias_filtradas if d.tipo == "sexual"),
        contagem_salarial=sum(1 for d in denuncias_filtradas if d.tipo == "salarial"),
        usuario=usuario,
        areas=AREAS_PADRAO,
        ranking=ranking_empresas(),
        todos_usuarios=Usuario.query.all()
    )


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
