from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///meubanco.db'
app.secret_key = "chave123"
db = SQLAlchemy(app)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    senha = db.Column(db.String(20), nullable=False)
    area = db.Column(db.String(50)) 

class Denuncia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)
    titulo = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(500), nullable=False)
    anonima = db.Column(db.String(10), nullable=False)
    empresa = db.Column(db.String(100)) 
    area_usuario = db.Column(db.String(50))
    cidade = db.Column(db.String(100))   # <-- ADICIONADO
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))

usuario_logado = None


@app.route('/')
def pagina_principal():
    global usuario_logado
    
    denuncias = Denuncia.query.all()
    total_denuncias = len(denuncias)
    
    contagem_moral = Denuncia.query.filter_by(tipo='moral').count()
    contagem_sexual = Denuncia.query.filter_by(tipo='sexual').count()
    contagem_salarial = Denuncia.query.filter_by(tipo='salarial').count()
    
    usuario = None
    if usuario_logado is not None:
        usuario = Usuario.query.get(usuario_logado)
    todos_usuarios = Usuario.query.all()
    
    areas = [
        'Tecnologia','Jurídico','Saúde','Educação','Administrativo','Marketing',
        'Vendas','Financeiro','Recursos Humanos','Engenharia','Design','Comunicação','Outros'
    ]

    return render_template(
        'index.html', 
        denuncias=denuncias,
        total_denuncias=total_denuncias,
        contagem_moral=contagem_moral,
        contagem_sexual=contagem_sexual,
        contagem_salarial=contagem_salarial,
        usuario=usuario,
        areas=areas,
        filtro_area='',
        todos_usuarios=todos_usuarios
    )


@app.route('/area/<area_nome>')
def filtrar_por_area(area_nome):
    global usuario_logado
    denuncias = Denuncia.query.filter_by(area_usuario=area_nome).all()

    total_denuncias = len(denuncias)
    contagem_moral = sum(1 for d in denuncias if d.tipo == "moral")
    contagem_sexual = sum(1 for d in denuncias if d.tipo == "sexual")
    contagem_salarial = sum(1 for d in denuncias if d.tipo == "salarial")

    usuario = Usuario.query.get(usuario_logado) if usuario_logado else None
    todos_usuarios = Usuario.query.all()

    areas = [
        'Tecnologia','Jurídico','Saúde','Educação','Administrativo','Marketing',
        'Vendas','Financeiro','Recursos Humanos','Engenharia','Design','Comunicação','Outros'
    ]
    
    return render_template(
        'index.html',
        denuncias=denuncias,
        total_denuncias=total_denuncias,
        contagem_moral=contagem_moral,
        contagem_sexual=contagem_sexual,
        contagem_salarial=contagem_salarial,
        usuario=usuario,
        areas=areas,
        filtro_area=area_nome,
        todos_usuarios=todos_usuarios
    )


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    global usuario_logado
    
    areas = [
        'Tecnologia','Jurídico','Saúde','Educação','Administrativo','Marketing',
        'Vendas','Financeiro','Recursos Humanos','Engenharia','Design','Comunicação','Outros'
    ]
    
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        area = request.form['area']
        
        if len(nome) < 2:
            return render_template('cadastro.html', erro='Nome muito curto!', areas=areas)
        
        if '@' not in email:
            return render_template('cadastro.html', erro='Email inválido!', areas=areas)
        
        if len(senha) < 4:
            return render_template('cadastro.html', erro='Senha muito curta!', areas=areas)
        
        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            return render_template('cadastro.html', erro='Email já cadastrado!', areas=areas)
        
        try:
            novo_usuario = Usuario(nome=nome, email=email, senha=senha, area=area)
            db.session.add(novo_usuario)
            db.session.commit()
            
            usuario_logado = novo_usuario.id
            return redirect('/')
            
        except:
            return render_template('cadastro.html', erro='Erro ao cadastrar!', areas=areas)
    
    return render_template('cadastro.html', areas=areas)


@app.route('/login', methods=['GET', 'POST'])
def login():
    global usuario_logado
    
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and usuario.senha == senha:
            usuario_logado = usuario.id
            return redirect('/')
        else:
            return render_template('login.html', erro='Email ou senha incorretos!')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    global usuario_logado
    usuario_logado = None
    return redirect('/')


@app.route('/nova_denuncia', methods=['GET', 'POST'])
def nova_denuncia():
    global usuario_logado
    
    if usuario_logado is None:
        return redirect('/login')
    
    usuario = Usuario.query.get(usuario_logado)
    
    if request.method == 'POST':
        tipo = request.form['tipo']
        titulo = request.form['titulo']
        descricao = request.form['descricao']
        empresa = request.form['empresa']
        cidade = request.form['cidade']
        anonima = request.form.get('anonima', 'nao')
        
        if not titulo or not descricao or not cidade:
            return render_template('nova_denuncia.html', erro='Preencha todos os campos obrigatórios!', usuario=usuario)
        
        if not empresa:
            empresa = 'Não informada'
        
        try:
            nova = Denuncia(
                tipo=tipo,
                titulo=titulo,
                descricao=descricao,
                empresa=empresa,
                cidade=cidade,
                anonima=anonima,
                area_usuario=usuario.area,
                usuario_id=usuario_logado
            )
            
            db.session.add(nova)
            db.session.commit()
            
            return redirect('/')
            
        except:
            return render_template('nova_denuncia.html', erro='Erro ao criar denúncia!', usuario=usuario)
    
    return render_template('nova_denuncia.html', usuario=usuario)


@app.route('/minhas_denuncias')
def minhas_denuncias():
    global usuario_logado
    
    if usuario_logado is None:
        return redirect('/login')
    
    usuario = Usuario.query.get(usuario_logado)
    if usuario is None:
        usuario_logado = None
        return redirect('/login')
    
    minhas_denuncias = Denuncia.query.filter_by(usuario_id=usuario.id).all()
    
    return render_template('minhas_denuncias.html', usuario=usuario, denuncias=minhas_denuncias)


@app.route('/filtrar_localizacao')
def filtrar_localizacao():
    cidade = request.args.get("cidade")

    if not cidade:
        flash("Preencha a cidade")
        return redirect("/")

    cidade = cidade.title()

    denuncias_filtradas = Denuncia.query.filter_by(cidade=cidade).all()
    
    return render_template(
        "index.html",
        denuncias=denuncias_filtradas,
        filtro_cidade=cidade,
        filtro_area=None,
        total_denuncias=len(denuncias_filtradas),
        contagem_moral=sum(1 for d in denuncias_filtradas if d.tipo == "moral"),
        contagem_sexual=sum(1 for d in denuncias_filtradas if d.tipo == "sexual"),
        contagem_salarial=sum(1 for d in denuncias_filtradas if d.tipo == "salarial"),
        areas=["RH", "TI", "Comercial", "Marketing"],
        todos_usuarios=Usuario.query.all()
    )


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True)
