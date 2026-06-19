from sqlalchemy import create_engine, text

def main():
    url = "postgresql://activia:activia@postgres:5432/activia_trace"
    engine = create_engine(url)
    with engine.connect() as conn:
        for t in ["carrera", "cohorte", "materia"]:
            r = conn.execute(text("select to_regclass('public.' || :t)",)).scalar()
            print(t, r)

if __name__ == '__main__':
    main()
