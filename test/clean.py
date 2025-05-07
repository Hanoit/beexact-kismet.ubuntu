import pandas as pd

def clean():
    # Leer el archivo CSV
    df = pd.read_csv('../data/providers.csv')

    # Borrar el campo 'id'
    df.drop(columns=['id'], inplace=True)

    # Eliminar valores duplicados en 'provider_name'
    df.drop_duplicates(subset=['provider_name'], inplace=True)

    # Guardar el archivo CSV limpio
    cleaned_file_path = '../data/providers.csv'
    df.to_csv(cleaned_file_path, index=False)

    print(f"Archivo limpio guardado en: {cleaned_file_path}")


if __name__ == '__main__':
    clean()