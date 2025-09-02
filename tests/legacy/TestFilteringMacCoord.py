import geopandas as gpd
import pandas as pd
from geopy.distance import geodesic

data = [
    {"devmac": "00:02:6F:A6:F5:AB", "strongest_signal":-83, "max_lat": 51.475219592, "max_lon": 5.764474665},
    {"devmac": "00:02:6F:A6:F5:AC", "strongest_signal":-85, "max_lat": 51.475219592, "max_lon": 5.764975000},  # Ajustado para estar cerca del primero
    {"devmac": "00:02:6F:A6:F5:AD", "strongest_signal":-80, "max_lat": 51.475220000, "max_lon": 5.764574000},  # Ajustado para estar cerca del primero
    {"devmac": "00:02:6F:A6:F5:AE", "strongest_signal":-70, "max_lat": 51.475219592, "max_lon": 5.764474665},  # Mismo lugar que el primero
    {"devmac": "00:02:6F:A1:F5:AE", "strongest_signal":-70, "max_lat": 51.475000000, "max_lon": 5.765000000},  # Further away, but could be close to others
    {"devmac": "00:02:6F:A6:F5:AE", "strongest_signal":-70, "max_lat": 51.475219592, "max_lon": 5.765474000}  # Cerca de los otros
]


def run_matrix():
    for i in range(len(data)):
        for j in range(len(data)):
            if i == j:
                continue
            point1 = (data[i].get("max_lon", None), data[i].get("max_lat", None))
            point2 = (data[j].get("max_lon", None), data[j].get("max_lat", None))
            # Calcular la distancia en metros
            distance = geodesic(point1, point2).meters
            print(f"Distance {data[i].get('devmac', None)} vs {data[j].get('devmac', None)} = {distance} meters")


def test_filtering():
    # Crear DataFrame
    df = pd.DataFrame(data)

    # Create point geometry
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.max_lon, df.max_lat), crs="EPSG:4326")

    # Convertir a un CRS proyectado adecuado para medir distancias en metros
    gdf = gdf.to_crs(epsg=3857)

    # Group by the first 8 positions of the MAC address (eliminar ':')
    gdf['mac_prefix'] = gdf['devmac'].str.replace(':', '').str[:8]

    def filter_within_distance(group, max_distance=50):
        # Crear la matriz de distancias
        distance_matrix = group.geometry.apply(lambda geom: group.distance(geom)).values

        # Iterate over matrix to remove records with weaker signal
        to_keep = set(range(len(group)))  # Indices de registros a mantener
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                if i in to_keep and j in to_keep:
                    if distance_matrix[i, j] <= max_distance:
                        # Compare signals and remove the one with weaker signal
                        if group.iloc[i]['strongest_signal'] > group.iloc[j]['strongest_signal']:
                            to_keep.discard(j)
                        else:
                            to_keep.discard(i)

        return group.iloc[list(to_keep)]

    # Aplicar el filtro dentro de cada grupo de mac_prefix
    filtered_gdf = gdf.groupby('mac_prefix').apply(filter_within_distance).reset_index(drop=True)

    # Ver el resultado filtrado
    print(filtered_gdf)


if __name__ == '__main__':
    # Ejecuta el caso de prueba
    run_matrix()
    test_filtering()
