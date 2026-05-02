

import sqlite3, hashlib
from datetime import date
DB = 'terrafisc.db'

def get_db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    return c

def h(p): return hashlib.sha256(p.encode()).hexdigest()

def init_db():
    conn = get_db(); c = conn.cursor()
    c.executescript('''
    CREATE TABLE IF NOT EXISTS bureau(
        bureau_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        nom          VARCHAR(80) NOT NULL,
        code         VARCHAR(10),
        description  TEXT
    );
    CREATE TABLE IF NOT EXISTS personnel(
        personnel_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        nom             VARCHAR(30) NOT NULL,
        prenom          VARCHAR(30),
        email           TEXT UNIQUE NOT NULL,
        mot_de_passe    TEXT NOT NULL,
        telephone       VARCHAR(15),
        dateNaissance   DATE,
        fonction        TEXT,
        role            TEXT NOT NULL CHECK(role IN ("chef_centre","chef_bureau","controleur","agent")),
        adresse         VARCHAR(100),
        superieur_id    INTEGER REFERENCES personnel(personnel_id),
        bureau_id       INTEGER REFERENCES bureau(bureau_id),
        annee_integration INTEGER,
    photo_profil      TEXT
    );
    CREATE TABLE IF NOT EXISTS activite(
        activite_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        nom           VARCHAR(100),
        type_activite VARCHAR(30),
        description   TEXT,
        dateDebut     DATE,
        dateFin       DATE,
        statut        VARCHAR(20) DEFAULT "Planifiee",
        bureau_id     INTEGER REFERENCES bureau(bureau_id),
        propose_par   INTEGER REFERENCES personnel(personnel_id),
        validee_par   INTEGER REFERENCES personnel(personnel_id)
    );
    CREATE TABLE IF NOT EXISTS proposition_activite(
        prop_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        description   TEXT,
        type_activite VARCHAR(30),
        date_prop     DATE,
        statut        VARCHAR(20) DEFAULT "En attente",
        propose_par   INTEGER REFERENCES personnel(personnel_id),
        destine_a     INTEGER REFERENCES personnel(personnel_id),
        commentaire_reponse TEXT
    );
    CREATE TABLE IF NOT EXISTS performance(
        performance_id INTEGER PRIMARY KEY AUTOINCREMENT,
        efficacite     INTEGER CHECK(efficacite BETWEEN 0 AND 100),
        note           INTEGER CHECK(note BETWEEN 0 AND 20),
        prime          VARCHAR(50),
        commentaire    TEXT,
        personnel_id   INTEGER REFERENCES personnel(personnel_id),
        evalue_par     INTEGER REFERENCES personnel(personnel_id),
        date_eval      DATE,
        mois           INTEGER,
        annee          INTEGER
    );
    CREATE TABLE IF NOT EXISTS employe_mois(
        em_id          INTEGER PRIMARY KEY AUTOINCREMENT,
        personnel_id   INTEGER REFERENCES personnel(personnel_id),
        mois           INTEGER NOT NULL,
        annee          INTEGER NOT NULL,
        note_finale    REAL,
        motif          TEXT,
        designe_par    INTEGER REFERENCES personnel(personnel_id),
        date_designation DATE,
        UNIQUE(mois, annee)
    );
    CREATE TABLE IF NOT EXISTS tache(
        tache_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        libelle      VARCHAR(100),
        description  TEXT,
        dateDebut    DATE,
        dateFin      DATE,
        statut       VARCHAR(30) DEFAULT "Non demarre",
        priorite     VARCHAR(20) DEFAULT "Normale",
        activite_id  INTEGER REFERENCES activite(activite_id),
        performance_id INTEGER REFERENCES performance(performance_id)
    );
    CREATE TABLE IF NOT EXISTS affecter(
        affect_id        INTEGER PRIMARY KEY AUTOINCREMENT,
        tache_id         INTEGER REFERENCES tache(tache_id),
        personnel_id     INTEGER REFERENCES personnel(personnel_id),
        role_affect      TEXT DEFAULT "Executant",
        date_affectation DATE,
        date_retrait     DATE,
        actif            INTEGER DEFAULT 1,
        assigne_par      INTEGER REFERENCES personnel(personnel_id)
    );
    CREATE TABLE IF NOT EXISTS notification(
        notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
        titre           TEXT NOT NULL,
        description     TEXT NOT NULL,
        type_notif      VARCHAR(30) DEFAULT "info",
        dateEnvoie      DATETIME DEFAULT CURRENT_TIMESTAMP,
        statut          VARCHAR(20) DEFAULT "Non lue",
        tache_id        INTEGER REFERENCES tache(tache_id),
        destinataire_id INTEGER REFERENCES personnel(personnel_id)
    );
    CREATE TABLE IF NOT EXISTS signalement(
        signalement_id INTEGER PRIMARY KEY AUTOINCREMENT,
        description    TEXT,
        dateEnvoie     DATE,
        statut         VARCHAR(30) DEFAULT "Ouvert",
        reponse        TEXT,
        personnel_id   INTEGER REFERENCES personnel(personnel_id),
        tache_id       INTEGER REFERENCES tache(tache_id),
        destine_a      INTEGER REFERENCES personnel(personnel_id)
    );
    CREATE TABLE IF NOT EXISTS idee(
        idee_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT,
        dateRecue   DATE,
        statut      VARCHAR(30) DEFAULT "Soumise",
        activite_id INTEGER REFERENCES activite(activite_id)
    );
    CREATE TABLE IF NOT EXISTS proposition_idee(
        idee_id      INTEGER REFERENCES idee(idee_id),
        personnel_id INTEGER REFERENCES personnel(personnel_id),
        PRIMARY KEY(idee_id, personnel_id)
    );
    CREATE TABLE IF NOT EXISTS avis(
        avis_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        commentaire  TEXT,
        note         INTEGER CHECK(note BETWEEN 1 AND 5),
        dateEnvoie   DATE,
        personnel_id INTEGER REFERENCES personnel(personnel_id)
    );
    CREATE TABLE IF NOT EXISTS compteRendu(
        cr_id        INTEGER PRIMARY KEY AUTOINCREMENT,
        dateRendue   DATE,
        contenu      TEXT NOT NULL,
        statut       VARCHAR(20) DEFAULT "Brouillon",
        personnel_id INTEGER REFERENCES personnel(personnel_id),
        tache_id     INTEGER REFERENCES tache(tache_id)
    );
    CREATE TABLE IF NOT EXISTS telepaiement(
        tp_id            INTEGER PRIMARY KEY AUTOINCREMENT,
        reference        TEXT UNIQUE NOT NULL,
        contribuable_nom TEXT NOT NULL,
        contribuable_nif TEXT,
        type_impot       TEXT NOT NULL,
        montant          REAL NOT NULL,
        montant_paye     REAL DEFAULT 0,
        statut           VARCHAR(30) DEFAULT "En attente",
        mode_paiement    TEXT,
        date_echeance    DATE,
        date_paiement    DATE,
        bureau_id        INTEGER REFERENCES bureau(bureau_id),
        agent_id         INTEGER REFERENCES personnel(personnel_id),
        notes            TEXT
    );
    ''');
    conn.commit(); conn.close()
    print('✅ Base de données créée avec succès')

def seed():
    conn = get_db(); c = conn.cursor()
    if c.execute('SELECT COUNT(*) FROM personnel').fetchone()[0] > 0:
        conn.close(); print('ℹ️  Données déjà présentes, seed ignoré'); return

    # ── 5 BUREAUX RÉELS ──
    bureaux = [
        ('Gestion des Contribuables et Services','GCS','Accueil, immatriculation, assistance et gestion des dossiers des contribuables'),
        ('Recouvrement','REC','Recouvrement des créances fiscales, mise en demeure, contraintes'),
        ('Bureau des Domaines','DOM','Gestion du domaine national, titres fonciers, concessions'),
        ('Conservation Foncière','COF','Conservation des titres de propriété, mutations, hypothèques'),
        ('Cadastre','CAD','Levés cadastraux, plans fonciers, fiscalité immobilière'),
    ]
    c.executemany('INSERT INTO bureau(nom,code,description) VALUES(?,?,?)', bureaux)

    pw = h('admin123')

    # ── CHEF DE CENTRE ──
    c.execute("INSERT INTO personnel(nom,prenom,email,mot_de_passe,fonction,role,bureau_id,telephone,annee_integration) VALUES(?,?,?,?,?,?,?,?,?)",
              ('DIALLO','PENDA','chef.centre@terrafisc.sn',pw,'Directeur du Centre des Impôts','chef_centre',1,'771000001',2015))
    cc = c.lastrowid

    # ── CHEFS DE BUREAU (1 par bureau) ──
    chefs_data = [
        ('DIOP','ABDOUL','cb.gcs@terrafisc.sn','Chef du Bureau GCS','chef_bureau',1),
        ('TOURE','Ibrahima','cb.rec@terrafisc.sn','Chef du Bureau Recouvrement','chef_bureau',2),
        ('MBENGUE','ABDOURAHMANE','cb.dom@terrafisc.sn','Chef du Bureau des Domaines','chef_bureau',3),
        ('DIOUF','ELHADJI IBRAHIMA','cb.cof@terrafisc.sn','Chef de la Conservation Foncière','chef_bureau',4),
        ('SECK','FALLOU','cb.cad@terrafisc.sn','Chef du Cadastre','chef_bureau',5),
    ]
    cb_ids = []
    for i,(nom,prenom,email,fonc,role,bid) in enumerate(chefs_data):
        c.execute("INSERT INTO personnel(nom,prenom,email,mot_de_passe,fonction,role,bureau_id,superieur_id,telephone,annee_integration) VALUES(?,?,?,?,?,?,?,?,?,?)",
                  (nom,prenom,email,pw,fonc,role,bid,cc,f'77200000{i+1}',2017+i))
        cb_ids.append(c.lastrowid)

    # ── CONTRÔLEURS (10 par bureau) ──
    ctrl_data = [
        ('KA','AMINATA','ctrl.gcs1@terrafisc.sn','Contrôleur',1,cb_ids[0]),
        ('DIAW','AMI','ctrl.gcs2@terrafisc.sn','Inspecteur',1,cb_ids[0]),
        ('KEBE','OUSMANE','ctrl.rec1@terrafisc.sn','Contrôleur',2,cb_ids[1]),
        ('DIALLO','MOUHAMADOUL MOUKHTAR','ctrl.rec2@terrafisc.sn','Inspecteur',2,cb_ids[1]),
        ('SOW','Pape','ctrl.dom1@terrafisc.sn','Contrôleur',3,cb_ids[2]),
        ('FAYE','Aminata','ctrl.dom2@terrafisc.sn','Inspecteur',3,cb_ids[2]),
        ('DIOP','Serigne','ctrl.cof1@terrafisc.sn','Contrôleur',4,cb_ids[3]),
        ('CISSE','Adja','ctrl.cof2@terrafisc.sn','Inspecteur',4,cb_ids[3]),
        ('TOURE','Boubacar','ctrl.cad1@terrafisc.sn','Contrôleur',5,cb_ids[4]),
        ('LY','Marième','ctrl.cad2@terrafisc.sn','Inspecteur',5,cb_ids[4]),
    ]
    ctrl_ids = []
    for i,(nom,prenom,email,fonc,bid,sup) in enumerate(ctrl_data):
        c.execute("INSERT INTO personnel(nom,prenom,email,mot_de_passe,fonction,role,bureau_id,superieur_id,telephone,annee_integration) VALUES(?,?,?,?,?,?,?,?,?,?)",
                  (nom,prenom,email,pw,fonc,'controleur',bid,sup,f'77300{i:04d}',2019+i%4))
        ctrl_ids.append(c.lastrowid)

    # ── AGENTS (30 par bureau) ──
    agents_data = [
        ('NGOM','Awa','agent.gcs1@terrafisc.sn','Agent d\'accueil',1,ctrl_ids[0]),
        ('BADJI','Lamine','agent.gcs2@terrafisc.sn','Agent de gestion',1,ctrl_ids[0]),
        ('BODIAN','Seynabou','agent.gcs3@terrafisc.sn','Téléconseiller',1,ctrl_ids[1]),
        ('DIEME','Aliou','agent.rec1@terrafisc.sn','Agent de recouvrement',2,ctrl_ids[2]),
        ('CAMARA','Khady','agent.rec2@terrafisc.sn','Agent de recouvrement',2,ctrl_ids[2]),
        ('MENDY','Ismaila','agent.rec3@terrafisc.sn','Agent de recouvrement',2,ctrl_ids[3]),
        ('BASSENE','Ndéye','agent.dom1@terrafisc.sn','Agent domanial',3,ctrl_ids[4]),
        ('DIATTA','Omar','agent.dom2@terrafisc.sn','Agent domanial',3,ctrl_ids[4]),
        ('MANGA','Madeleine','agent.dom3@terrafisc.sn','Agent domanial',3,ctrl_ids[5]),
        ('GOMIS','Pascal','agent.cof1@terrafisc.sn','Agent foncier',4,ctrl_ids[6]),
        ('SAMBOU','Bernadette','agent.cof2@terrafisc.sn','Agent foncier',4,ctrl_ids[6]),
        ('TENDENG','Joseph','agent.cof3@terrafisc.sn','Agent foncier',4,ctrl_ids[7]),
        ('SANE','Ousmane','agent.cad1@terrafisc.sn','Géomètre',5,ctrl_ids[8]),
        ('BADIANE','Célestine','agent.cad2@terrafisc.sn','Technicien cadastral',5,ctrl_ids[8]),
        ('COLY','Augustin','agent.cad3@terrafisc.sn','Technicien cadastral',5,ctrl_ids[9]),
    ]
    agent_ids = []
    for i,(nom,prenom,email,fonc,bid,sup) in enumerate(agents_data):
        c.execute("INSERT INTO personnel(nom,prenom,email,mot_de_passe,fonction,role,bureau_id,superieur_id,telephone,annee_integration) VALUES(?,?,?,?,?,?,?,?,?,?)",
                  (nom,prenom,email,pw,fonc,'agent',bid,sup,f'77400{i:04d}',2020+i%5))
        agent_ids.append(c.lastrowid)

    # ── ACTIVITÉS PAR BUREAU ──
    activites_data = [
        ('Campagne immatriculation NIF 2025','Campagne','Sensibilisation et immatriculation des contribuables non identifiés','2025-04-01','2025-06-30','En cours',1),
        ('Audit des dossiers GCS Q1','Audit','Vérification et mise à jour des dossiers contribuables','2025-03-01','2025-03-31','Terminee',1),
        ('Opération recouvrement arrières T1','Mission','Recouvrement des créances fiscales du 1er trimestre','2025-04-10','2025-05-31','En cours',2),
        ('Formation procédures de mise en demeure','Formation','Formation des agents sur les nouvelles procédures','2025-05-15','2025-05-17','Planifiee',2),
        ('Révision des titres fonciers zone industrielle','Mission','Mise à jour du registre des titres fonciers','2025-04-01','2025-07-31','En cours',3),
        ('Atelier foncier rural','Atelier','Sensibilisation sur la sécurisation foncière rurale','2025-06-01','2025-06-03','Planifiee',3),
        ('Conservation titres quartier Almadies','Mission','Traitement des mutations en attente','2025-04-15','2025-05-30','En cours',4),
        ('Informatisation registre hypothèques','Projet','Numérisation des actes hypothécaires','2025-01-01','2025-12-31','En cours',4),
        ('Levé cadastral zone périurbaine','Mission','Mise à jour du plan cadastral','2025-05-01','2025-08-31','Planifiee',5),
        ('Mise à jour base fiscalité immobilière','Mission','Actualisation des valeurs locatives','2025-04-01','2025-06-30','En cours',5),
    ]
    act_ids = []
    for t in activites_data:
        c.execute('INSERT INTO activite(nom,type_activite,description,dateDebut,dateFin,statut,bureau_id) VALUES(?,?,?,?,?,?,?)',t)
        act_ids.append(c.lastrowid)

    # ── TÂCHES ──
    taches_data = [
        ('Préparation formulaires NIF','Imprimer et distribuer les formulaires','2025-04-01','2025-04-05','Terminee','Haute',act_ids[0]),
        ('Saisie des nouvelles immatriculations','Saisir les données dans le système','2025-04-06','2025-06-30','En cours','Normale',act_ids[0]),
        ('Rapport audit Q1 GCS','Rédiger le rapport final de l\'audit','2025-03-25','2025-03-31','Terminee','Haute',act_ids[1]),
        ('Identification créanciers défaillants','Lister les contribuables en arriéré','2025-04-10','2025-04-20','Terminee','Haute',act_ids[2]),
        ('Émission mises en demeure','Préparer et envoyer les mises en demeure','2025-04-20','2025-05-10','En cours','Haute',act_ids[2]),
        ('TDR formation mise en demeure','Rédiger les termes de référence','2025-04-20','2025-04-30','En cours','Normale',act_ids[3]),
        ('Convocations formation','Envoyer les convocations aux participants','2025-05-01','2025-05-10','Non demarre','Normale',act_ids[3]),
        ('Inventaire titres fonciers zone ind.','Dresser la liste des titres concernés','2025-04-01','2025-04-15','Terminee','Haute',act_ids[4]),
        ('Mise à jour registre foncier','Actualiser le registre informatisé','2025-04-15','2025-07-31','En cours','Normale',act_ids[4]),
        ('Traitement mutations en attente','Traiter les dossiers de mutation','2025-04-15','2025-05-30','En cours','Haute',act_ids[6]),
        ('Scan actes hypothécaires','Numériser les actes du registre A','2025-01-15','2025-06-30','En cours','Normale',act_ids[7]),
        ('Actualisation valeurs locatives','Mettre à jour les données fiscales','2025-04-01','2025-06-30','En cours','Haute',act_ids[9]),
    ]
    tache_ids = []
    for t in taches_data:
        c.execute('INSERT INTO tache(libelle,description,dateDebut,dateFin,statut,priorite,activite_id) VALUES(?,?,?,?,?,?,?)',t)
        tache_ids.append(c.lastrowid)

    # ── AFFECTATIONS ──
    affects = [
        (tache_ids[0],agent_ids[0],'Principal','2025-04-01',ctrl_ids[0]),
        (tache_ids[1],agent_ids[1],'Executant','2025-04-06',ctrl_ids[0]),
        (tache_ids[1],agent_ids[2],'Executant','2025-04-06',ctrl_ids[0]),
        (tache_ids[2],agent_ids[1],'Principal','2025-03-20',ctrl_ids[1]),
        (tache_ids[3],agent_ids[3],'Principal','2025-04-10',ctrl_ids[2]),
        (tache_ids[4],agent_ids[4],'Executant','2025-04-20',ctrl_ids[2]),
        (tache_ids[4],agent_ids[5],'Executant','2025-04-20',ctrl_ids[3]),
        (tache_ids[5],agent_ids[6],'Principal','2025-04-20',ctrl_ids[4]),
        (tache_ids[7],agent_ids[6],'Principal','2025-04-01',ctrl_ids[4]),
        (tache_ids[8],agent_ids[7],'Executant','2025-04-15',ctrl_ids[5]),
        (tache_ids[9],agent_ids[9],'Principal','2025-04-15',ctrl_ids[6]),
        (tache_ids[10],agent_ids[10],'Executant','2025-01-15',ctrl_ids[7]),
        (tache_ids[11],agent_ids[13],'Principal','2025-04-01',ctrl_ids[9]),
    ]
    for (tid,pid,role,dt,sup) in affects:
        c.execute('INSERT INTO affecter(tache_id,personnel_id,role_affect,date_affectation,actif,assigne_par) VALUES(?,?,?,?,1,?)',(tid,pid,role,dt,sup))
        c.execute("INSERT INTO notification(titre,description,type_notif,tache_id,destinataire_id) VALUES(?,?,?,?,?)",
                  ('Nouvelle tâche assignée','Vous avez une nouvelle tâche. Consultez votre tableau de bord.','tache',tid,pid))

    # ── PERFORMANCES ──
    perfs = [
        (90,18,'75000 FCFA','Excellent travail sur la campagne NIF',agent_ids[0],ctrl_ids[0],'2025-03-31',3,2025),
        (82,16,'50000 FCFA','Bonne rigueur documentaire',agent_ids[1],ctrl_ids[0],'2025-03-31',3,2025),
        (95,19,'100000 FCFA','Performance exceptionnelle sur le recouvrement',agent_ids[3],ctrl_ids[2],'2025-03-31',3,2025),
        (78,15,None,'Résultats satisfaisants, à améliorer',agent_ids[4],ctrl_ids[2],'2025-03-31',3,2025),
        (88,17,'75000 FCFA','Très bonne gestion des titres fonciers',agent_ids[6],ctrl_ids[4],'2025-03-31',3,2025),
        (70,14,None,'Quelques retards à corriger',agent_ids[7],ctrl_ids[5],'2025-03-31',3,2025),
        (92,18,'75000 FCFA','Excellent sur les mutations foncières',agent_ids[9],ctrl_ids[6],'2025-03-31',3,2025),
        (85,17,'50000 FCFA','Bon travail sur la numérisation',agent_ids[13],ctrl_ids[9],'2025-03-31',3,2025),
    ]
    perf_ids = []
    for p in perfs:
        c.execute('INSERT INTO performance(efficacite,note,prime,commentaire,personnel_id,evalue_par,date_eval,mois,annee) VALUES(?,?,?,?,?,?,?,?,?)',p)
        perf_ids.append(c.lastrowid)

    # ── EMPLOYÉ DU MOIS ── (3 derniers mois)
    em_data = [
        (agent_ids[3], 1, 2025, 18.5, 'Recouvrement exceptionnel : 98% du quota atteint, zéro réclamation', cb_ids[1]),
        (agent_ids[0], 2, 2025, 17.8, 'Meilleure performance sur les immatriculations NIF du mois', cb_ids[0]),
        (agent_ids[9], 3, 2025, 18.0, 'Excellence dans le traitement des mutations et délais respectés', cb_ids[3]),
    ]
    for (pid, mois, annee, note, motif, desig) in em_data:
        c.execute('INSERT INTO employe_mois(personnel_id,mois,annee,note_finale,motif,designe_par,date_designation) VALUES(?,?,?,?,?,?,?)',
                  (pid,mois,annee,note,motif,desig,'2025-'+str(mois).zfill(2)+'-28'))

    # ── TÉLÉPAIEMENTS ──
    tp_data = [
        ('TP2025-001','SOCOCIM Industries','SN000001','Impôt sur les Sociétés',45000000,45000000,'Paye','Virement bancaire','2025-03-31','2025-03-28',1,agent_ids[0],None),
        ('TP2025-002','AUCHAN Sénégal','SN000002','TVA mensuelle',12500000,12500000,'Paye','Mobile Money (Wave)','2025-04-20','2025-04-18',1,agent_ids[1],None),
        ('TP2025-003','Groupe Maurel & Prom','SN000003','Taxe foncière',3200000,0,'En attente',None,'2025-04-30',None,5,agent_ids[13],'Contribuable en cours de constitution de dossier'),
        ('TP2025-004','SENELEC','SN000004','Acompte IS',18000000,18000000,'Paye','Virement BCEAO','2025-03-31','2025-03-30',2,agent_ids[3],None),
        ('TP2025-005','Air Sénégal','SN000005','Taxe sur les salaires',2800000,1400000,'Partiel','Mobile Money (Orange)','2025-04-15','2025-04-14',2,agent_ids[4],'Solde restant dû : 1 400 000 FCFA'),
        ('TP2025-006','SDE (Société des Eaux)','SN000006','TVA mensuelle',8900000,0,'En retard',None,'2025-04-10',None,2,agent_ids[5],'Mise en demeure émise le 15/04/2025'),
        ('TP2025-007','CBAO Banque','SN000007','Taxe foncière TF n°1234',950000,950000,'Paye','Carte bancaire','2025-03-15','2025-03-14',4,agent_ids[9],None),
        ('TP2025-008','Résidence Les Almadies','SN000008','Contribution foncière bâtie',2100000,0,'En attente',None,'2025-05-31',None,4,agent_ids[10],'Dossier complet reçu'),
        ('TP2025-009','Cabinet Géomètre Diop','SN000009','Droits de bornage',350000,350000,'Paye','Mobile Money (Wave)','2025-04-01','2025-04-01',5,agent_ids[13],None),
        ('TP2025-010','Lotissement SICAP','SN000010','Taxe de plus-value immobilière',5600000,5600000,'Paye','Virement bancaire','2025-04-05','2025-04-04',3,agent_ids[6],None),
    ]
    for tp in tp_data:
        c.execute('INSERT INTO telepaiement(reference,contribuable_nom,contribuable_nif,type_impot,montant,montant_paye,statut,mode_paiement,date_echeance,date_paiement,bureau_id,agent_id,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)', tp)

    # ── SIGNALEMENTS ──
    c.execute("INSERT INTO signalement(description,dateEnvoie,statut,personnel_id,tache_id,destine_a) VALUES(?,?,?,?,?,?)",
              ('Manque de données dans le système pour 3 contribuables inscrits. Impossible de finaliser la saisie.','2025-04-22','Ouvert',agent_ids[1],tache_ids[1],ctrl_ids[0]))
    c.execute("INSERT INTO signalement(description,dateEnvoie,statut,personnel_id,tache_id,destine_a) VALUES(?,?,?,?,?,?)",
              ('Contribuable TP2025-006 (SDE) non joignable. Risque de dépassement de délai.','2025-04-20','Ouvert',agent_ids[5],tache_ids[4],ctrl_ids[3]))

    # ── PROPOSITIONS ──
    c.execute("INSERT INTO proposition_activite(description,type_activite,date_prop,statut,propose_par,destine_a) VALUES(?,?,?,?,?,?)",
              ('Organiser une journée portes ouvertes pour les nouveaux contribuables sur la procédure d\'immatriculation en ligne.','Atelier','2025-04-18','En attente',ctrl_ids[0],cb_ids[0]))
    c.execute("INSERT INTO proposition_activite(description,type_activite,date_prop,statut,propose_par,destine_a) VALUES(?,?,?,?,?,?)",
              ('Mettre en place un tableau de suivi partagé pour les mises en demeure en cours afin d\'éviter les doublons.','Mission','2025-04-20','Acceptee',ctrl_ids[2],cb_ids[1]))

    # ── AVIS ──
    c.execute("INSERT INTO avis(commentaire,note,dateEnvoie,personnel_id) VALUES(?,?,?,?)",('Interface claire, la section télépaiement est très utile.',5,'2025-04-25',agent_ids[0]))
    c.execute("INSERT INTO avis(commentaire,note,dateEnvoie,personnel_id) VALUES(?,?,?,?)",('Ajouter un export Excel des télépaiements.',4,'2025-04-26',agent_ids[3]))
    c.execute("INSERT INTO avis(commentaire,note,dateEnvoie,personnel_id) VALUES(?,?,?,?)",('Le module employé du mois motive vraiment l\'équipe !',5,'2025-04-27',agent_ids[9]))

    conn.commit(); conn.close()
    print('✅ Données insérées avec succès\n')
    print('━'*58)
    print('📋 COMPTES DE CONNEXION (mot de passe : admin123)')
    print('━'*58)
    print('  chef.centre@terrafisc.sn   →  Chef de Centre')
    print('  cb.gcs@terrafisc.sn        →  Chef Bureau GCS')
    print('  cb.rec@terrafisc.sn        →  Chef Bureau Recouvrement')
    print('  cb.dom@terrafisc.sn        →  Chef Bureau Domaines')
    print('  cb.cof@terrafisc.sn        →  Chef Conservation Foncière')
    print('  cb.cad@terrafisc.sn        →  Chef Cadastre')
    print('  ctrl.gcs1@terrafisc.sn     →  Contrôleur GCS')
    print('  ctrl.rec1@terrafisc.sn     →  Contrôleur Recouvrement')
    print('  agent.gcs1@terrafisc.sn    →  Agent GCS')
    print('  agent.rec1@terrafisc.sn    →  Agent Recouvrement')
    print('━'*58)

init_db()
seed()
from flask import Flask, request, jsonify, render_template_string, session
from flask_cors import CORS
import sqlite3, threading, hashlib, json
from datetime import date, datetime

app = Flask(__name__)
app.secret_key = 'terrafisc_2025_secret'
CORS(app, supports_credentials=True)

def h(p): return hashlib.sha256(p.encode()).hexdigest()

def gen_email(nom, prenom):
    import unicodedata, re as _re
    def clean(s):
        s = unicodedata.normalize('NFD', s or '')
        s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
        return _re.sub(r'[^a-z0-9]', '', s.lower())
    n = clean(nom); p = clean(prenom)
    base = f"{p}.{n}@terrafisc.sn" if p else f"{n}@terrafisc.sn"
    # Check uniqueness
    existing = qry("SELECT email FROM personnel WHERE email LIKE ?", (f"{p}.{n}%@terrafisc.sn",))
    if not any(r['email'] == base for r in existing):
        return base
    i = 2
    while True:
        candidate = f"{p}.{n}{i}@terrafisc.sn"
        if not any(r['email'] == candidate for r in existing):
            return candidate
        i += 1

def qry(sql, params=(), one=False):
    conn = get_db()
    rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
    conn.close()
    return rows[0] if (one and rows) else (None if (one and not rows) else rows)

def exe(sql, params=()):
    conn = get_db(); cur = conn.execute(sql, params); conn.commit(); lid = cur.lastrowid; conn.close(); return lid

def notif(titre, desc, type_n, dest_id, tache_id=None):
    if dest_id:
        exe('INSERT INTO notification(titre,description,type_notif,tache_id,destinataire_id) VALUES(?,?,?,?,?)',
            (titre, desc, type_n, tache_id, dest_id))

def uid(): return session.get('user_id')
def role(): return session.get('role')
def auth(): return 'user_id' in session

MOIS_FR = ['','Janvier','Février','Mars','Avril','Mai','Juin','Juillet','Août','Septembre','Octobre','Novembre','Décembre']

# ═══════════════════════════════════════════════════════
#  AUTH
# ═══════════════════════════════════════════════════════
@app.route('/api/login', methods=['POST'])
def login():
    d = request.json
    u = qry('SELECT * FROM personnel WHERE email=? AND mot_de_passe=?', (d['email'], h(d['password'])), one=True)
    if not u: return jsonify({'error': 'Email ou mot de passe incorrect'}), 401
    session['user_id'] = u['personnel_id']
    session['role'] = u['role']
    u.pop('mot_de_passe', None)
    return jsonify(u)

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear(); return jsonify({'ok': True})

@app.route('/api/change-password', methods=['POST'])
def change_password():
    if not auth(): return jsonify({'error': 'Non authentifié'}), 401
    d = request.json
    u = qry('SELECT mot_de_passe FROM personnel WHERE personnel_id=?', (uid(),), one=True)
    if not u or u['mot_de_passe'] != h(d['old_password']):
        return jsonify({'error': 'Mot de passe actuel incorrect'}), 403
    exe('UPDATE personnel SET mot_de_passe=? WHERE personnel_id=?', (h(d['new_password']), uid()))
    return jsonify({'ok': True})

@app.route('/api/personnel/', methods=['GET'])
def get_personnel_by_id(pid):
    if not auth(): return jsonify({'error': 'Non authentifié'}), 401
    row = qry('SELECT p.*,b.nom bureau_nom FROM personnel p LEFT JOIN bureau b ON p.bureau_id=b.bureau_id WHERE p.personnel_id=?', (pid,), one=True)
    if row: row.pop('mot_de_passe', None)
    return jsonify(row or {})

# ═══════════════════════════════════════════════════════
#  DASHBOARD
# ═══════════════════════════════════════════════════════
@app.route('/api/dashboard')
def dashboard():
    if not auth(): return jsonify({'error': 'Non authentifié'}), 401
    r = role(); u = uid()
    nb_notifs = qry("SELECT COUNT(*) c FROM notification WHERE destinataire_id=? AND statut='Non lue'", (u,), one=True)['c']

    if r == 'chef_centre':
        return jsonify({
            'nb_bureaux': qry('SELECT COUNT(*) c FROM bureau', one=True)['c'],
            'nb_personnel': qry('SELECT COUNT(*) c FROM personnel', one=True)['c'],
            'nb_activites': qry('SELECT COUNT(*) c FROM activite', one=True)['c'],
            'nb_taches': qry('SELECT COUNT(*) c FROM tache', one=True)['c'],
            'nb_notifs': nb_notifs,
            'taches_statut': qry('SELECT statut, COUNT(*) n FROM tache GROUP BY statut'),
            'activites_statut': qry('SELECT statut, COUNT(*) n FROM activite GROUP BY statut'),
            'bureaux_activites': qry('SELECT b.nom, COUNT(a.activite_id) n FROM bureau b LEFT JOIN activite a ON b.bureau_id=a.bureau_id GROUP BY b.nom'),
            'top_performances': qry('SELECT p.nom,p.prenom,pf.note,pf.efficacite,b.nom bureau_nom FROM performance pf JOIN personnel p ON pf.personnel_id=p.personnel_id JOIN bureau b ON p.bureau_id=b.bureau_id ORDER BY pf.note DESC LIMIT 8'),
            'employe_mois': qry('SELECT em.*,p.nom,p.prenom,b.nom bureau_nom FROM employe_mois em JOIN personnel p ON em.personnel_id=p.personnel_id JOIN bureau b ON p.bureau_id=b.bureau_id ORDER BY em.annee DESC,em.mois DESC LIMIT 3'),
            'tp_stats': qry("SELECT statut,COUNT(*) n,SUM(montant) total FROM telepaiement GROUP BY statut"),
        })
    elif r == 'chef_bureau':
        bid = qry('SELECT bureau_id FROM personnel WHERE personnel_id=?', (u,), one=True)['bureau_id']
        return jsonify({
            'nb_controleurs': qry('SELECT COUNT(*) c FROM personnel WHERE superieur_id=? AND role="controleur"', (u,), one=True)['c'],
            'nb_agents': qry('SELECT COUNT(*) c FROM personnel WHERE bureau_id=? AND role="agent"', (bid,), one=True)['c'],
            'nb_activites': qry('SELECT COUNT(*) c FROM activite WHERE bureau_id=?', (bid,), one=True)['c'],
            'nb_taches': qry('SELECT COUNT(*) c FROM tache t JOIN activite a ON t.activite_id=a.activite_id WHERE a.bureau_id=?', (bid,), one=True)['c'],
            'nb_notifs': nb_notifs,
            'taches_statut': qry('SELECT t.statut,COUNT(*) n FROM tache t JOIN activite a ON t.activite_id=a.activite_id WHERE a.bureau_id=? GROUP BY t.statut', (bid,)),
            'propositions_recues': qry("SELECT COUNT(*) c FROM proposition_activite WHERE destine_a=? AND statut='En attente'", (u,), one=True)['c'],
            'signalements_ouverts': qry("SELECT COUNT(*) c FROM signalement WHERE destine_a=? AND statut='Ouvert'", (u,), one=True)['c'],
            'employe_mois': qry('SELECT em.*,p.nom,p.prenom FROM employe_mois em JOIN personnel p ON em.personnel_id=p.personnel_id JOIN bureau b ON p.bureau_id=b.bureau_id WHERE p.bureau_id=? ORDER BY em.annee DESC,em.mois DESC LIMIT 3', (bid,)),
            'tp_bureau': qry('SELECT statut,COUNT(*) n,SUM(montant) total FROM telepaiement WHERE bureau_id=? GROUP BY statut', (bid,)),
        })
    elif r == 'controleur':
        return jsonify({
            'nb_agents': qry('SELECT COUNT(*) c FROM personnel WHERE superieur_id=?', (u,), one=True)['c'],
            'nb_taches_assignees': qry('SELECT COUNT(DISTINCT tache_id) c FROM affecter WHERE assigne_par=? AND actif=1', (u,), one=True)['c'],
            'nb_notifs': nb_notifs,
            'taches_statut': qry('SELECT t.statut,COUNT(*) n FROM tache t JOIN affecter af ON t.tache_id=af.tache_id WHERE af.assigne_par=? AND af.actif=1 GROUP BY t.statut', (u,)),
            'signalements_recus': qry("SELECT COUNT(*) c FROM signalement WHERE destine_a=? AND statut='Ouvert'", (u,), one=True)['c'],
            'mes_taches': qry('SELECT t.*,a.nom act_nom FROM tache t JOIN affecter af ON t.tache_id=af.tache_id JOIN activite a ON t.activite_id=a.activite_id WHERE af.personnel_id=? AND af.actif=1 ORDER BY t.dateFin', (u,)),
        })
    else:  # agent
        return jsonify({
            'nb_taches': qry('SELECT COUNT(*) c FROM affecter WHERE personnel_id=? AND actif=1', (u,), one=True)['c'],
            'nb_terminees': qry("SELECT COUNT(*) c FROM tache t JOIN affecter af ON t.tache_id=af.tache_id WHERE af.personnel_id=? AND af.actif=1 AND t.statut='Terminee'", (u,), one=True)['c'],
            'nb_notifs': nb_notifs,
            'ma_performance': qry('SELECT * FROM performance WHERE personnel_id=? ORDER BY date_eval DESC LIMIT 1', (u,), one=True),
            'mes_taches': qry('SELECT t.*,a.nom act_nom FROM tache t JOIN affecter af ON t.tache_id=af.tache_id JOIN activite a ON t.activite_id=a.activite_id WHERE af.personnel_id=? AND af.actif=1 ORDER BY t.dateFin', (u,)),
            'employe_mois_courant': qry('SELECT em.*,p.nom,p.prenom FROM employe_mois em JOIN personnel p ON em.personnel_id=p.personnel_id WHERE em.mois=? AND em.annee=?', (date.today().month, date.today().year), one=True),
        })

# ═══════════════════════════════════════════════════════
#  BUREAUX
# ═══════════════════════════════════════════════════════
@app.route('/api/bureaux', methods=['GET', 'POST'])
def bureaux():
    if not auth(): return jsonify({'error': 'Non authentifié'}), 401
    if request.method == 'POST':
        if role() != 'chef_centre': return jsonify({'error': 'Non autorisé'}), 403
        d = request.json
        lid = exe('INSERT INTO bureau(nom,code,description) VALUES(?,?,?)', (d['nom'], d.get('code'), d.get('description')))
        return jsonify({'bureau_id': lid}), 201
    return jsonify(qry('SELECT b.*, (SELECT COUNT(*) FROM personnel WHERE bureau_id=b.bureau_id) nb_pers, (SELECT COUNT(*) FROM activite WHERE bureau_id=b.bureau_id) nb_act FROM bureau b'))

# ═══════════════════════════════════════════════════════
#  PERSONNEL
# ═══════════════════════════════════════════════════════
@app.route('/api/personnel', methods=['GET', 'POST'])
def personnel_list():
    if not auth(): return jsonify({'error': 'Non authentifié'}), 401
    u = uid(); r = role()
    if request.method == 'POST':
        if r not in ('chef_centre', 'chef_bureau'): return jsonify({'error': 'Non autorisé'}), 403
        d = request.json
        # Auto-generate email from nom/prenom
        email_auto = gen_email(d['nom'], d.get('prenom', ''))
        pwd_init = d.get('password', 'terrafisc2025')
        lid = exe('INSERT INTO personnel(nom,prenom,email,mot_de_passe,telephone,dateNaissance,fonction,role,adresse,superieur_id,bureau_id,annee_integration) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
            (d['nom'],d.get('prenom'),email_auto,h(pwd_init),d.get('telephone'),d.get('dateNaissance'),d.get('fonction'),d['role'],d.get('adresse'),d.get('superieur_id'),d.get('bureau_id'),d.get('annee_integration',date.today().year)))
        notif('Bienvenue sur TERRAFISC', f"Vos identifiants : Email: {email_auto} | Mot de passe: {pwd_init}", 'info', lid)
        return jsonify({'personnel_id': lid, 'email': email_auto, 'password': pwd_init}), 201
    if r == 'chef_centre':
        rows = qry('SELECT p.*,b.nom bureau_nom,s.nom sup_nom FROM personnel p LEFT JOIN bureau b ON p.bureau_id=b.bureau_id LEFT JOIN personnel s ON p.superieur_id=s.personnel_id ORDER BY p.role,p.nom')
    elif r == 'chef_bureau':
        bid = qry('SELECT bureau_id FROM personnel WHERE personnel_id=?', (u,), one=True)['bureau_id']
        rows = qry('SELECT p.*,b.nom bureau_nom FROM personnel p LEFT JOIN bureau b ON p.bureau_id=b.bureau_id WHERE p.bureau_id=? ORDER BY p.role,p.nom', (bid,))
    elif r == 'controleur':
        rows = qry('SELECT p.*,b.nom bureau_nom FROM personnel p LEFT JOIN bureau b ON p.bureau_id=b.bureau_id WHERE p.superieur_id=?', (u,))
    else:
        rows = qry('SELECT p.*,b.nom bureau_nom FROM personnel p LEFT JOIN bureau b ON p.bureau_id=b.bureau_id WHERE p.personnel_id=?', (u,))
    for row in rows: row.pop('mot_de_passe', None)
    return jsonify(rows)

@app.route('/api/personnel//photo', methods=['POST'])
def upload_photo(pid):
    if not auth(): return jsonify({'error': 'Non authentifié'}), 401
    if uid() != pid and role() not in ('chef_centre', 'chef_bureau'):
        return jsonify({'error': 'Non autorisé'}), 403
    d = request.json
    exe('UPDATE personnel SET photo_profil=? WHERE personnel_id=?', (d.get('photo'), pid))
    return jsonify({'ok': True})

@app.route('/api/personnel/', methods=['PUT', 'DELETE'])
def personnel_detail(pid):
    if not auth(): return jsonify({'error': 'Non authentifié'}), 401
    r = role(); u = uid()
    if request.method == 'DELETE':
        # Seul le chef de centre peut supprimer un personnel
        if r != 'chef_centre': return jsonify({'error': 'Non autorisé'}), 403
        exe('DELETE FROM personnel WHERE personnel_id=?', (pid,)); return jsonify({'ok': True})
    # PUT : chacun peut modifier ses propres infos; chef_centre/chef_bureau peuvent tout modifier
    if u != pid and r not in ('chef_centre', 'chef_bureau'):
        return jsonify({'error': 'Non autorisé'}), 403
    d = request.json
    # Champs modifiables par soi-même
    self_fields = ['nom', 'prenom', 'telephone', 'adresse', 'dateNaissance', 'photo_profil']
    # Champs admin uniquement
    admin_fields = ['email', 'fonction', 'role', 'superieur_id', 'bureau_id']
    sets, vals = [], []
    for f in self_fields:
        if f in d:
            sets.append(f'{f}=?'); vals.append(d[f])
    if r in ('chef_centre', 'chef_bureau'):
        for f in admin_fields:
            if f in d:
                sets.append(f'{f}=?'); vals.append(d[f])
    if not sets: return jsonify({'error': 'Rien à modifier'}), 400
    vals.append(pid)
    exe(f'UPDATE personnel SET {",".join(sets)} WHERE personnel_id=?', vals)
    return jsonify({'ok': True})

# ═══════════════════════════════════════════════════════
#  ACTIVITÉS
# ═══════════════════════════════════════════════════════
@app.route('/api/activites', methods=['GET', 'POST'])
def activites():
    if not auth(): return jsonify({'error': 'Non authentifié'}), 401
    u = uid(); r = role()
    if request.method == 'POST':
        if r not in ('chef_centre', 'chef_bureau'): return jsonify({'error': 'Non autorisé'}), 403
        d = request.json
        lid = exe('INSERT INTO activite(nom,type_activite,description,dateDebut,dateFin,statut,bureau_id,propose_par) VALUES(?,?,?,?,?,?,?,?)',
            (d['nom'],d.get('type_activite'),d.get('description'),d.get('dateDebut'),d.get('dateFin'),d.get('statut','Planifiee'),d.get('bureau_id'),u))
        return jsonify({'activite_id': lid}), 201
    base = 'SELECT a.*,b.nom bureau_nom,(SELECT COUNT(*) FROM tache WHERE activite_id=a.activite_id) nb_taches,(SELECT COUNT(*) FROM tache WHERE activite_id=a.activite_id AND statut="Terminee") nb_ok FROM activite a LEFT JOIN bureau b ON a.bureau_id=b.bureau_id'
    if r == 'chef_centre':
        return jsonify(qry(base + ' ORDER BY a.dateDebut DESC'))
    elif r == 'chef_bureau':
        bid = qry('SELECT bureau_id FROM personnel WHERE personnel_id=?', (u,), one=True)['bureau_id']
        return jsonify(qry(base + ' WHERE a.bureau_id=? ORDER BY a.dateDebut DESC', (bid,)))
    else:
        return jsonify(qry(base + ' JOIN tache t ON a.activite_id=t.activite_id JOIN affecter af ON t.tache_id=af.tache_id WHERE af.personnel_id=? AND af.actif=1 GROUP BY a.activite_id', (u,)))

@app.route('/api/activites/', methods=['PUT', 'DELETE'])
def activite_detail(aid):
    if not auth() or role() not in ('chef_centre', 'chef_bureau'): return jsonify({'error': 'Non autorisé'}), 403
    if request.method == 'DELETE':
        exe('DELETE FROM activite WHERE activite_id=?', (aid,)); return jsonify({'ok': True})
    d = request.json
    exe('UPDATE activite SET nom=?,type_activite=?,description=?,dateDebut=?,dateFin=?,statut=? WHERE activite_id=?',
        (d.get('nom'),d.get('type_activite'),d.get('description'),d.get('dateDebut'),d.get('dateFin'),d.get('statut'),aid))
    return jsonify({'ok': True})

@app.route('/api/activites//gantt')
def gantt(aid):
    if not auth(): return jsonify({'error': 'Non authentifié'}), 401
    return jsonify({
        'activite': qry('SELECT * FROM activite WHERE activite_id=?', (aid,), one=True),
        'taches': qry('SELECT t.*,GROUP_CONCAT(p.nom||\'  \'||COALESCE(p.prenom,\'\')) agents FROM tache t LEFT JOIN affecter af ON t.tache_id=af.tache_id AND af.actif=1 LEFT JOIN personnel p ON af.personnel_id=p.personnel_id WHERE t.activite_id=? GROUP BY t.tache_id ORDER BY t.dateDebut', (aid,))
    })

# ═══════════════════════════════════════════════════════
#  TÂCHES
# ═══════════════════════════════════════════════════════
@app.route('/api/taches', methods=['GET', 'POST'])
def taches():
    if not auth(): return jsonify({'error': 'Non authentifié'}), 401
    u = uid(); r = role()
    if request.method == 'POST':
        if r not in ('chef_bureau', 'controleur'): return jsonify({'error': 'Non autorisé'}), 403
        d = request.json
        lid = exe('INSERT INTO tache(libelle,description,dateDebut,dateFin,statut,priorite,activite_id) VALUES(?,?,?,?,?,?,?)',
            (d['libelle'],d.get('description'),d.get('dateDebut'),d.get('dateFin'),d.get('statut','Non demarre'),d.get('priorite','Normale'),d.get('activite_id')))
        return jsonify({'tache_id': lid}), 201
    base = 'SELECT t.*,a.nom act_nom,GROUP_CONCAT(p.nom||\'  \'||COALESCE(p.prenom,\'\')) agents FROM tache t LEFT JOIN activite a ON t.activite_id=a.activite_id LEFT JOIN affecter af ON t.tache_id=af.tache_id AND af.actif=1 LEFT JOIN personnel p ON af.personnel_id=p.personnel_id'
    if r == 'chef_centre':
        return jsonify(qry(base + ' GROUP BY t.tache_id ORDER BY t.dateFin'))
    elif r == 'chef_bureau':
        bid = qry('SELECT bureau_id FROM personnel WHERE personnel_id=?', (u,), one=True)['bureau_id']
        return jsonify(qry(base + ' WHERE a.bureau_id=? GROUP BY t.tache_id ORDER BY t.dateFin', (bid,)))
    elif r == 'controleur':
        return jsonify(qry(base + ' WHERE af.assigne_par=? OR af.personnel_id=? GROUP BY t.tache_id ORDER BY t.dateFin', (u, u)))
    else:
        return jsonify(qry('SELECT t.*,a.nom act_nom,af.role_affect FROM tache t JOIN affecter af ON t.tache_id=af.tache_id JOIN activite a ON t.activite_id=a.activite_id WHERE af.personnel_id=? AND af.actif=1 ORDER BY t.dateFin', (u,)))

@app.route('/api/taches/', methods=['PUT', 'DELETE'])
def tache_detail(tid):
    if not auth(): return jsonify({'error': 'Non authentifié'}), 401
    u = uid(); r = role()
    if request.method == 'DELETE':
        if r not in ('chef_bureau', 'controleur'): return jsonify({'error': 'Non autorisé'}), 403
        exe('DELETE FROM tache WHERE tache_id=?', (tid,)); return jsonify({'ok': True})
    d = request.json; old = qry('SELECT * FROM tache WHERE tache_id=?', (tid,), one=True)
    if r == 'agent':
        exe('UPDATE tache SET statut=? WHERE tache_id=?', (d.get('statut', old['statut']), tid))
    else:
        exe('UPDATE tache SET libelle=?,description=?,dateDebut=?,dateFin=?,statut=?,priorite=? WHERE tache_id=?',
            (d.get('libelle',old['libelle']),d.get('description',old['description']),d.get('dateDebut',old['dateDebut']),d.get('dateFin',old['dateFin']),d.get('statut',old['statut']),d.get('priorite',old['priorite']),tid))
    if d.get('statut') and d['statut'] != old.get('statut'):
        for ag in qry('SELECT personnel_id FROM affecter WHERE tache_id=? AND actif=1', (tid,)):
            notif('Mise à jour tâche', f'Tâche "{old["libelle"]}" → statut : {d["statut"]}', 'tache', ag['personnel_id'], tid)
    return jsonify({'ok': True})

@app.route('/api/taches//affecter', methods=['POST'])
def affecter(tid):
    if not auth() or role() not in ('chef_centre', 'chef_bureau', 'controleur'): return jsonify({'error': 'Non autorisé'}), 403
    u = uid(); d = request.json; dest = int(d['personnel_id'])
    subs = [s['personnel_id'] for s in qry('SELECT personnel_id FROM personnel WHERE superieur_id=?', (u,))]
    if role() != 'chef_centre' and dest not in subs:
        return jsonify({'error': 'Vous ne pouvez affecter qu\'à vos subordonnés directs'}), 403
    exe('INSERT INTO affecter(tache_id,personnel_id,role_affect,date_affectation,actif,assigne_par) VALUES(?,?,?,?,1,?)',
        (tid, dest, d.get('role', 'Executant'), str(date.today()), u))
    tl = qry('SELECT libelle FROM tache WHERE tache_id=?', (tid,), one=True)
    notif(f'Nouvelle tâche assignée', f'Vous avez été affecté(e) à : "{tl["libelle"]}". Consultez votre tableau de bord.', 'tache', dest, tid)
    return jsonify({'ok': True})

@app.route('/api/taches//retirer/', methods=['DELETE'])
def retirer(tid, pid):
    if not auth() or role() not in ('chef_centre', 'chef_bureau', 'controleur'): return jsonify({'error': 'Non autorisé'}), 403
    exe('UPDATE affecter SET actif=0,date_retrait=? WHERE tache_id=? AND personnel_id=?', (str(date.today()), tid, pid))
    notif('Retrait d\'affectation', 'Vous avez été retiré(e) d\'une tâche.', 'info', pid, tid)
    return jsonify({'ok': True})

@app.route('/api/taches//historique')
def historique_tache(tid):
    if not auth(): return jsonify({'error': 'Non authentifié'}), 401
    return jsonify(qry('SELECT af.*,p.nom||\'  \'||COALESCE(p.prenom,\'\') agent_nom,s.nom||\'  \'||COALESCE(s.prenom,\'\') sup_nom FROM affecter af JOIN personnel p ON af.personnel_id=p.personnel_id LEFT JOIN personnel s ON af.assigne_par=s.personnel_id WHERE af.tache_id=? ORDER BY af.date_affectation DESC', (tid,)))

# ═══════════════════════════════════════════════════════
#  PERFORMANCES
# ═══════════════════════════════════════════════════════
@app.route('/api/performances', methods=['GET', 'POST'])
def performances():
    if not auth(): return jsonify({'error': 'Non authentifié'}), 401
    u = uid(); r = role()
    if request.method == 'POST':
        if r not in ('chef_bureau', 'controleur'): return jsonify({'error': 'Non autorisé'}), 403
        d = request.json; dest = int(d['personnel_id'])
        subs = [s['personnel_id'] for s in qry('SELECT personnel_id FROM personnel WHERE superieur_id=?', (u,))]
        if dest not in subs: return jsonify({'error': 'Vous ne pouvez évaluer que vos subordonnés'}), 403
        m = date.today().month; an = date.today().year
        lid = exe('INSERT INTO performance(efficacite,note,prime,commentaire,personnel_id,evalue_par,date_eval,mois,annee) VALUES(?,?,?,?,?,?,?,?,?)',
            (d.get('efficacite'),d.get('note'),d.get('prime'),d.get('commentaire'),dest,u,str(date.today()),m,an))
        notif('Nouvelle évaluation reçue', f'Vous avez reçu une évaluation pour {MOIS_FR[m]} {an}.', 'performance', dest)
        return jsonify({'performance_id': lid}), 201
    if r == 'chef_centre':
        return jsonify(qry('SELECT pf.*,p.nom,p.prenom,b.nom bureau_nom,e.nom eval_nom FROM performance pf JOIN personnel p ON pf.personnel_id=p.personnel_id JOIN bureau b ON p.bureau_id=b.bureau_id LEFT JOIN personnel e ON pf.evalue_par=e.personnel_id ORDER BY pf.date_eval DESC'))
    elif r == 'chef_bureau':
        bid = qry('SELECT bureau_id FROM personnel WHERE personnel_id=?', (u,), one=True)['bureau_id']
        return jsonify(qry('SELECT pf.*,p.nom,p.prenom,e.nom eval_nom FROM performance pf JOIN personnel p ON pf.personnel_id=p.personnel_id LEFT JOIN personnel e ON pf.evalue_par=e.personnel_id WHERE p.bureau_id=? ORDER BY pf.date_eval DESC', (bid,)))
    elif r == 'controleur':
        return jsonify(qry('SELECT pf.*,p.nom,p.prenom FROM performance pf JOIN personnel p ON pf.personnel_id=p.personnel_id WHERE pf.evalue_par=? ORDER BY pf.date_eval DESC', (u,)))
    else:
        return jsonify(qry('SELECT pf.*,e.nom eval_nom FROM performance pf LEFT JOIN personnel e ON pf.evalue_par=e.personnel_id WHERE pf.personnel_id=? ORDER BY pf.date_eval DESC', (u,)))

# ═══════════════════════════════════════════════════════
#  EMPLOYÉ DU MOIS
# ═══════════════════════════════════════════════════════
@app.route('/api/employe-mois', methods=['GET', 'POST'])
def employe_mois():
    if not auth(): return jsonify({'error': 'Non authentifié'}), 401
    if request.method == 'POST':
        if role() not in ('chef_centre', 'chef_bureau'): return jsonify({'error': 'Non autorisé'}), 403
        d = request.json
        m = int(d.get('mois', date.today().month))
        an = int(d.get('annee', date.today().year))
        # Remplacer si déjà existant pour ce mois/année
        existing = qry('SELECT em_id FROM employe_mois WHERE mois=? AND annee=?', (m, an), one=True)
        if existing:
            exe('UPDATE employe_mois SET personnel_id=?,note_finale=?,motif=?,designe_par=?,date_designation=? WHERE mois=? AND annee=?',
                (d['personnel_id'],d.get('note_finale'),d.get('motif'),uid(),str(date.today()),m,an))
        else:
            exe('INSERT INTO employe_mois(personnel_id,mois,annee,note_finale,motif,designe_par,date_designation) VALUES(?,?,?,?,?,?,?)',
                (d['personnel_id'],m,an,d.get('note_finale'),d.get('motif'),uid(),str(date.today())))
        notif('🏆 Employé du mois !', f'Félicitations ! Vous êtes désigné(e) Employé du mois de {MOIS_FR[m]} {an}.', 'employe_mois', int(d['personnel_id']))
        return jsonify({'ok': True}), 201
    return jsonify(qry('SELECT em.*,p.nom,p.prenom,p.fonction,b.nom bureau_nom,d.nom designateur_nom FROM employe_mois em JOIN personnel p ON em.personnel_id=p.personnel_id JOIN bureau b ON p.bureau_id=b.bureau_id LEFT JOIN personnel d ON em.designe_par=d.personnel_id ORDER BY em.annee DESC,em.mois DESC'))

# ═══════════════════════════════════════════════════════
#  TÉLÉPAIEMENT
# ═══════════════════════════════════════════════════════
@app.route('/api/telepaiements', methods=['GET', 'POST'])
def telepaiements():
    if not auth(): return jsonify({'error': 'Non authentifié'}), 401
    u = uid(); r = role()
    if request.method == 'POST':
        if r not in ('chef_bureau', 'controleur', 'agent'): return jsonify({'error': 'Non autorisé'}), 403
        d = request.json
        ref = f'TP{date.today().year}-{str(exe("SELECT COUNT(*) c FROM telepaiement", ())+1).zfill(3)}'
        lid = exe('INSERT INTO telepaiement(reference,contribuable_nom,contribuable_nif,type_impot,montant,montant_paye,statut,mode_paiement,date_echeance,bureau_id,agent_id,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
            (ref,d['contribuable_nom'],d.get('contribuable_nif'),d['type_impot'],d['montant'],d.get('montant_paye',0),d.get('statut','En attente'),d.get('mode_paiement'),d.get('date_echeance'),d.get('bureau_id'),u,d.get('notes')))
        return jsonify({'tp_id': lid, 'reference': ref}), 201
    base = 'SELECT tp.*,b.nom bureau_nom,p.nom agent_nom,p.prenom agent_prenom FROM telepaiement tp LEFT JOIN bureau b ON tp.bureau_id=b.bureau_id LEFT JOIN personnel p ON tp.agent_id=p.personnel_id'
    if r == 'chef_centre':
        return jsonify(qry(base + ' ORDER BY tp.date_echeance'))
    elif r == 'chef_bureau':
        bid = qry('SELECT bureau_id FROM personnel WHERE personnel_id=?', (u,), one=True)['bureau_id']
        return jsonify(qry(base + ' WHERE tp.bureau_id=? ORDER BY tp.date_echeance', (bid,)))
    else:
        bid = qry('SELECT bureau_id FROM personnel WHERE personnel_id=?', (u,), one=True)['bureau_id']
        return jsonify(qry(base + ' WHERE tp.bureau_id=? ORDER BY tp.date_echeance', (bid,)))

@app.route('/api/telepaiements/', methods=['PUT'])
def telepaiement_update(tid):
    if not auth(): return jsonify({'error': 'Non authentifié'}), 401
    d = request.json
    exe('UPDATE telepaiement SET statut=?,montant_paye=?,mode_paiement=?,date_paiement=?,notes=? WHERE tp_id=?',
        (d.get('statut'),d.get('montant_paye'),d.get('mode_paiement'),d.get('date_paiement',str(date.today())),d.get('notes'),tid))
    return jsonify({'ok': True})

@app.route('/api/telepaiements/stats')
def tp_stats():
    if not auth(): return jsonify({'error': 'Non authentifié'}), 401
    return jsonify({
        'par_statut': qry('SELECT statut,COUNT(*) n,ROUND(SUM(montant)/1000000,2) total_m FROM telepaiement GROUP BY statut'),
        'par_bureau': qry('SELECT b.nom,COUNT(*) n,ROUND(SUM(tp.montant)/1000000,2) total_m,ROUND(SUM(tp.montant_paye)/1000000,2) paye_m FROM telepaiement tp JOIN bureau b ON tp.bureau_id=b.bureau_id GROUP BY b.nom'),
        'par_type': qry('SELECT type_impot,COUNT(*) n,ROUND(SUM(montant)/1000000,2) total_m FROM telepaiement GROUP BY type_impot ORDER BY total_m DESC'),
        'total_attendu': qry('SELECT ROUND(SUM(montant)/1000000,2) v FROM telepaiement', one=True)['v'],
        'total_recouvre': qry('SELECT ROUND(SUM(montant_paye)/1000000,2) v FROM telepaiement', one=True)['v'],
    })

# ═══════════════════════════════════════════════════════
#  NOTIFICATIONS, SIGNALEMENTS, PROPOSITIONS, AVIS, CR
# ═══════════════════════════════════════════════════════
@app.route('/api/notifications')
def notifications():
    if not auth(): return jsonify({'error': 'Non authentifié'}), 401
    return jsonify(qry('SELECT n.*,t.libelle tache_libelle FROM notification n LEFT JOIN tache t ON n.tache_id=t.tache_id WHERE n.destinataire_id=? ORDER BY n.dateEnvoie DESC', (uid(),)))

@app.route('/api/notifications//lire', methods=['PUT'])
def lire_notif(nid):
    exe("UPDATE notification SET statut='Lue' WHERE notification_id=?", (nid,)); return jsonify({'ok': True})

@app.route('/api/notifications/tout-lire', methods=['PUT'])
def tout_lire():
    if not auth(): return jsonify({'error': 'Non authentifié'}), 401
    exe("UPDATE notification SET statut='Lue' WHERE destinataire_id=?", (uid(),)); return jsonify({'ok': True})

@app.route('/api/signalements', methods=['GET', 'POST'])
def signalements():
    if not auth(): return jsonify({'error': 'Non authentifié'}), 401
    u = uid(); r = role()
    if request.method == 'POST':
        d = request.json
        sup = qry('SELECT superieur_id FROM personnel WHERE personnel_id=?', (u,), one=True)['superieur_id']
        lid = exe('INSERT INTO signalement(description,dateEnvoie,statut,personnel_id,tache_id,destine_a) VALUES(?,?,?,?,?,?)',
            (d['description'], str(date.today()), 'Ouvert', u, d.get('tache_id'), sup))
        if sup: notif('Nouveau signalement', 'Un collaborateur a émis un signalement. Consultez la section signalements.', 'alerte', sup)
        return jsonify({'signalement_id': lid}), 201
    if r == 'chef_centre':
        return jsonify(qry('SELECT s.*,p.nom auteur,t.libelle tache_lib FROM signalement s LEFT JOIN personnel p ON s.personnel_id=p.personnel_id LEFT JOIN tache t ON s.tache_id=t.tache_id ORDER BY s.dateEnvoie DESC'))
    elif r in ('chef_bureau', 'controleur'):
        return jsonify(qry('SELECT s.*,p.nom auteur,t.libelle tache_lib FROM signalement s LEFT JOIN personnel p ON s.personnel_id=p.personnel_id LEFT JOIN tache t ON s.tache_id=t.tache_id WHERE s.destine_a=? ORDER BY s.dateEnvoie DESC', (u,)))
    else:
        return jsonify(qry('SELECT s.*,t.libelle tache_lib FROM signalement s LEFT JOIN tache t ON s.tache_id=t.tache_id WHERE s.personnel_id=? ORDER BY s.dateEnvoie DESC', (u,)))

@app.route('/api/signalements//repondre', methods=['PUT'])
def repondre_signal(sid):
    d = request.json
    exe('UPDATE signalement SET reponse=?,statut=? WHERE signalement_id=?', (d.get('reponse'), d.get('statut', 'Traite'), sid))
    sig = qry('SELECT personnel_id FROM signalement WHERE signalement_id=?', (sid,), one=True)
    notif('Signalement traité', 'Votre signalement a reçu une réponse.', 'info', sig['personnel_id'])
    return jsonify({'ok': True})

@app.route('/api/propositions', methods=['GET', 'POST'])
def propositions():
    if not auth(): return jsonify({'error': 'Non authentifié'}), 401
    u = uid(); r = role()
    if request.method == 'POST':
        if r not in ('controleur', 'agent'): return jsonify({'error': 'Non autorisé'}), 403
        d = request.json
        sup = qry('SELECT superieur_id FROM personnel WHERE personnel_id=?', (u,), one=True)['superieur_id']
        if not sup: return jsonify({'error': 'Pas de supérieur défini'}), 400
        lid = exe('INSERT INTO proposition_activite(description,type_activite,date_prop,propose_par,destine_a) VALUES(?,?,?,?,?)',
            (d['description'], d.get('type_activite', 'Mission'), str(date.today()), u, sup))
        notif('Nouvelle proposition d\'activité', 'Un collaborateur vous a soumis une proposition d\'activité.', 'proposition', sup)
        return jsonify({'prop_id': lid}), 201
    if r in ('chef_centre', 'chef_bureau'):
        return jsonify(qry('SELECT pa.*,p.nom proposeur,p.prenom proposeur_prenom FROM proposition_activite pa JOIN personnel p ON pa.propose_par=p.personnel_id WHERE pa.destine_a=? ORDER BY pa.date_prop DESC', (u,)))
    else:
        return jsonify(qry('SELECT pa.*,p.nom destinataire FROM proposition_activite pa JOIN personnel p ON pa.destine_a=p.personnel_id WHERE pa.propose_par=? ORDER BY pa.date_prop DESC', (u,)))

@app.route('/api/propositions//repondre', methods=['PUT'])
def repondre_prop(pid):
    d = request.json
    exe('UPDATE proposition_activite SET statut=?,commentaire_reponse=? WHERE prop_id=?', (d.get('statut'), d.get('commentaire'), pid))
    prop = qry('SELECT propose_par,statut FROM proposition_activite WHERE prop_id=?', (pid,), one=True)
    notif(f'Proposition {d.get("statut","").lower()}', f'Votre proposition d\'activité a été {d.get("statut","").lower()}.', 'info', prop['propose_par'])
    return jsonify({'ok': True})

@app.route('/api/avis', methods=['GET', 'POST'])
def avis():
    if not auth(): return jsonify({'error': 'Non authentifié'}), 401
    if request.method == 'POST':
        d = request.json
        exe('INSERT INTO avis(commentaire,note,dateEnvoie,personnel_id) VALUES(?,?,?,?)', (d.get('commentaire'), d.get('note'), str(date.today()), uid()))
        return jsonify({'ok': True}), 201
    return jsonify(qry('SELECT av.*,p.nom,p.prenom,b.nom bureau_nom FROM avis av LEFT JOIN personnel p ON av.personnel_id=p.personnel_id LEFT JOIN bureau b ON p.bureau_id=b.bureau_id ORDER BY av.dateEnvoie DESC'))

@app.route('/api/comptes-rendus', methods=['GET', 'POST'])
def comptes_rendus():
    if not auth(): return jsonify({'error': 'Non authentifié'}), 401
    u = uid(); r = role()
    if request.method == 'POST':
        if r == 'chef_centre': return jsonify({'error': 'Le chef de centre ne peut pas soumettre de comptes-rendus'}), 403
        d = request.json
        exe('INSERT INTO compteRendu(dateRendue,contenu,statut,personnel_id,tache_id) VALUES(?,?,?,?,?)',
            (str(date.today()), d['contenu'], d.get('statut', 'Soumis'), u, d.get('tache_id')))
        sup = qry('SELECT superieur_id FROM personnel WHERE personnel_id=?', (u,), one=True)['superieur_id']
        if sup: notif('Nouveau compte-rendu', 'Un collaborateur vient de soumettre un compte-rendu.', 'info', sup)
        return jsonify({'ok': True}), 201
    if r == 'chef_centre':
        # Le chef de centre voit TOUS les comptes-rendus
        return jsonify(qry('SELECT cr.*,p.nom,p.prenom,b.nom bureau_nom,t.libelle tache_lib FROM compteRendu cr LEFT JOIN personnel p ON cr.personnel_id=p.personnel_id LEFT JOIN bureau b ON p.bureau_id=b.bureau_id LEFT JOIN tache t ON cr.tache_id=t.tache_id ORDER BY cr.dateRendue DESC'))
    elif r == 'chef_bureau':
        # Le chef de bureau voit les CR de son bureau (contrôleurs + agents)
        bid = qry('SELECT bureau_id FROM personnel WHERE personnel_id=?', (u,), one=True)['bureau_id']
        return jsonify(qry('SELECT cr.*,p.nom,p.prenom,b.nom bureau_nom,t.libelle tache_lib FROM compteRendu cr JOIN personnel p ON cr.personnel_id=p.personnel_id LEFT JOIN bureau b ON p.bureau_id=b.bureau_id LEFT JOIN tache t ON cr.tache_id=t.tache_id WHERE p.bureau_id=? ORDER BY cr.dateRendue DESC', (bid,)))
    elif r == 'controleur':
        # Le contrôleur voit les CR de ses agents directs
        return jsonify(qry('SELECT cr.*,p.nom,p.prenom,t.libelle tache_lib FROM compteRendu cr JOIN personnel p ON cr.personnel_id=p.personnel_id LEFT JOIN tache t ON cr.tache_id=t.tache_id WHERE p.superieur_id=? ORDER BY cr.dateRendue DESC', (u,)))
    else:
        # L'agent voit uniquement ses propres CR
        return jsonify(qry('SELECT cr.*,t.libelle tache_lib FROM compteRendu cr LEFT JOIN tache t ON cr.tache_id=t.tache_id WHERE cr.personnel_id=? ORDER BY cr.dateRendue DESC', (u,)))
