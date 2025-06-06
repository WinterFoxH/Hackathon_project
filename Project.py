import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import mean_squared_error, accuracy_score, classification_report
import os
import re  # Do konwersji czasu
import matplotlib.pyplot as plt
import seaborn as sns

# --- Konfiguracja Stylu Wykresów ---
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)  # Domyślny rozmiar wykresów

# --- Konfiguracja Ścieżki Danych ---
DATA_DIR = "C:/University/Lab_IoT/Project"


# --- Funkcje Pomocnicze ---
def load_data(csv_name):
    path = os.path.join(DATA_DIR, csv_name)
    if not os.path.exists(path):
        print(f"BŁĄD: Plik {path} nie został znaleziony.")
        return None
    return pd.read_csv(path)


def time_to_milliseconds(time_str):
    if pd.isna(time_str) or not isinstance(time_str, str):
        return np.nan
    if '\\N' in time_str:
        return np.nan
    parts = time_str.split(':')
    try:
        if len(parts) == 2:
            minutes = int(parts[0])
            seconds_millis = float(parts[1])
            return int(minutes * 60 * 1000 + seconds_millis * 1000)
        elif len(parts) == 1:
            seconds_millis = float(parts[0])
            return int(seconds_millis * 1000)
        else:
            return np.nan
    except ValueError:
        return np.nan


# --- Wczytanie Głównych Zbiorów Danych ---
print("Wczytywanie danych...")
circuits_df = load_data("circuits.csv")
races_df = load_data("races.csv")
drivers_df = load_data("drivers.csv")
constructors_df = load_data("constructors.csv")
results_df = load_data("results.csv")
lap_times_df = load_data("lap_times.csv")
pit_stops_df = load_data("pit_stops.csv")
qualifying_df = load_data("qualifying.csv")

if any(df is None for df in
       [circuits_df, races_df, drivers_df, constructors_df, results_df, lap_times_df, pit_stops_df, qualifying_df]):
    print("Nie udało się wczytać jednego lub więcej kluczowych plików. Zakończenie programu.")
    exit()
print("Dane wczytane pomyślnie.\n")


# --- 1. Predykcja czasu okrążenia (lap_times.csv) ---
def predict_future_lap_time():
    print("--- Zadanie 1: Predykcja Czasu Okrążenia ---")
    if lap_times_df is None or races_df is None:
        print("Brak danych. Pomijanie zadania.")
        return

    data = pd.merge(lap_times_df, races_df[['raceId', 'year', 'circuitId']], on='raceId')
    features = ['raceId', 'driverId', 'lap', 'position', 'year', 'circuitId']
    target = 'milliseconds'
    data_cleaned = data.dropna(subset=features + [target])

    if data_cleaned.empty:
        print("Brak danych po czyszczeniu.")
        return

    X = data_cleaned[features]
    y = data_cleaned[target]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1, max_depth=10, min_samples_leaf=5)
    print("Trenowanie modelu czasu okrążenia...")
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    print(f"RMSE dla predykcji czasu okrążenia: {rmse:.2f} ms")

    if not X_test.empty:
        sample_future_lap_data = X_test.sample(1, random_state=42).copy()
        sample_future_lap_data['lap'] += 5
        sample_future_lap_data['year'] = races_df['year'].max() + 1
        predicted_time = model.predict(sample_future_lap_data)
        print(
            f"Przykładowa predykcja czasu dla 'przyszłego' okrążenia (dane: {sample_future_lap_data.iloc[0].to_dict()}): {predicted_time[0]:.0f} ms")

    # --- WIZUALIZACJA I ANALIZA (Zadanie 1) ---
    if not data_cleaned.empty:
        plt.figure(figsize=(12, 6))
        sns.histplot(data_cleaned['milliseconds'] / 1000, kde=True, bins=50)
        plt.title('Rozkład czasów okrążeń (w sekundach)')
        plt.xlabel('Czas okrążenia (s)')
        plt.ylabel('Liczba okrążeń')
        plt.tight_layout()
        plt.show()

        # Porównanie rzeczywistych vs przewidywanych wartości (na małej próbce dla czytelności)
        sample_size = min(500, len(y_test))  # Ograniczamy do 500 punktów dla czytelności wykresu
        indices = np.random.choice(y_test.index, sample_size, replace=False)

        plt.figure(figsize=(12, 6))
        plt.scatter(y_test.loc[indices] / 1000, predictions[y_test.index.get_indexer(indices)] / 1000, alpha=0.5,
                    s=10)  # s=10 rozmiar punktu
        plt.plot([min(y_test.loc[indices] / 1000), max(y_test.loc[indices] / 1000)],
                 [min(y_test.loc[indices] / 1000), max(y_test.loc[indices] / 1000)],
                 'r--', lw=2, label='Idealna predykcja')
        plt.title(f'Porównanie rzeczywistych i przewidywanych czasów okrążeń (próbka {sample_size} punktów)')
        plt.xlabel('Rzeczywisty czas okrążenia (s)')
        plt.ylabel('Przewidywany czas okrążenia (s)')
        plt.legend()
        plt.tight_layout()
        plt.show()

        # Cechy o największym znaczeniu
        if hasattr(model, 'feature_importances_'):
            importances = pd.Series(model.feature_importances_, index=X_train.columns).sort_values(ascending=False)
            plt.figure(figsize=(10, 6))
            sns.barplot(x=importances.values, y=importances.index)
            plt.title('Ważność cech dla modelu czasu okrążenia')
            plt.xlabel('Ważność')
            plt.ylabel('Cecha')
            plt.tight_layout()
            plt.show()
    print("-" * 30 + "\n")


# --- 2. Predykcja zmniejszania się czasu pit stopów (pit_stops.csv) ---
def predict_pit_stop_duration_decrease():
    print("--- Zadanie 2: Predykcja Czasu Trwania Pit Stopu ---")
    if pit_stops_df is None or races_df is None:
        print("Brak danych. Pomijanie zadania.")
        return

    data = pd.merge(pit_stops_df, races_df[['raceId', 'year', 'circuitId']], on='raceId')
    features = ['raceId', 'driverId', 'stop', 'lap', 'year', 'circuitId']
    target = 'milliseconds'
    data_cleaned = data.dropna(subset=features + [target])

    if data_cleaned.empty:
        print("Brak danych po czyszczeniu.")
        return

    X = data_cleaned[features]
    y = data_cleaned[target]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1, max_depth=10, min_samples_leaf=5)
    print("Trenowanie modelu czasu pit stopu...")
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    print(f"RMSE dla predykcji czasu pit stopu: {rmse:.2f} ms")

    simulated_pit_stop_years = []
    simulated_pit_stop_durations = []

    if not X_test.empty:
        max_year_in_test_data = X_test['year'].max()
        mask_max_year_in_test = (X_test['year'] == max_year_in_test_data)
        y_test_for_max_year = y_test[mask_max_year_in_test]
        current_year_avg = y_test_for_max_year.mean() if not y_test_for_max_year.empty else np.nan

        sample_pit_stop_base = X_test.sample(1, random_state=42).copy()
        print("\nSymulacja predykcji czasu pit stopu dla przyszłych lat (dla przykładowych danych):")
        base_year = races_df['year'].max()
        for future_year_offset in range(1, 6):  # Symulacja na 5 lat w przyszłość
            future_year = base_year + future_year_offset
            future_data_sample = sample_pit_stop_base.copy()
            future_data_sample['year'] = future_year
            future_data_sample = future_data_sample[features]
            predicted_duration = model.predict(future_data_sample)
            print(f"  Rok {future_year}: Przewidywany czas pit stopu: {predicted_duration[0]:.0f} ms")
            simulated_pit_stop_years.append(future_year)
            simulated_pit_stop_durations.append(predicted_duration[0])

        if not np.isnan(current_year_avg):
            print(
                f"Średni czas pit stopu w ostatnim roku danych testowych ({max_year_in_test_data}): {current_year_avg:.0f} ms")
        else:
            print(
                f"Nie można obliczyć średniego czasu pit stopu dla ostatniego roku danych testowych ({max_year_in_test_data}).")

    # --- WIZUALIZACJA I ANALIZA (Zadanie 2) ---
    if not data_cleaned.empty:
        # Trend historyczny czasów pit stopów
        avg_pit_time_per_year = data_cleaned.groupby('year')['milliseconds'].mean() / 1000  # w sekundach
        plt.figure(figsize=(12, 6))
        avg_pit_time_per_year.plot(marker='o', linestyle='-')
        plt.title('Średni czas trwania pit stopu na przestrzeni lat')
        plt.xlabel('Rok')
        plt.ylabel('Średni czas pit stopu (s)')
        plt.grid(True)
        plt.tight_layout()
        plt.show()

        # Wykres symulowanych przyszłych czasów pit stopów
        if simulated_pit_stop_years:
            plt.figure(figsize=(10, 6))
            plt.plot(simulated_pit_stop_years, [d / 1000 for d in simulated_pit_stop_durations], marker='o',
                     linestyle='--')
            plt.title('Symulowana predykcja czasu pit stopu dla przyszłych lat (na podstawie próbki)')
            plt.xlabel('Rok')
            plt.ylabel('Przewidywany czas pit stopu (s)')
            plt.xticks(simulated_pit_stop_years)
            plt.grid(True)
            plt.tight_layout()
            plt.show()

        # Cechy o największym znaczeniu
        if hasattr(model, 'feature_importances_'):
            importances_pit = pd.Series(model.feature_importances_, index=X_train.columns).sort_values(ascending=False)
            plt.figure(figsize=(10, 6))
            sns.barplot(x=importances_pit.values, y=importances_pit.index)
            plt.title('Ważność cech dla modelu czasu pit stopu')
            plt.xlabel('Ważność')
            plt.ylabel('Cecha')
            plt.tight_layout()
            plt.show()
    print("-" * 30 + "\n")


# --- 3. Predykcja najszybszego okrążenia w wyścigu (na podstawie qualifying.csv) ---
def predict_fastest_lap_holder():
    print("--- Zadanie 3: Predykcja Autora Najszybszego Okrążenia ---")
    if results_df is None or qualifying_df is None or races_df is None or drivers_df is None:
        print("Brak danych. Pomijanie zadania.")
        return

    q_df_prep = qualifying_df.copy()
    for col in ['q1', 'q2', 'q3']:
        if col in q_df_prep.columns:
            q_df_prep[col + '_ms'] = q_df_prep[col].apply(time_to_milliseconds)
    q_df_prep['best_quali_ms'] = q_df_prep[['q1_ms', 'q2_ms', 'q3_ms']].min(axis=1)
    if 'position' in q_df_prep.columns:
        q_df_prep = q_df_prep.rename(columns={'position': 'position_qualify'})
    else:
        q_df_prep['position_qualify'] = np.nan
    q_data_to_merge = q_df_prep[['raceId', 'driverId', 'constructorId', 'position_qualify', 'best_quali_ms']]

    res_df_prep = results_df.copy()
    res_df_prep['fastestLapTime_ms'] = res_df_prep['fastestLapTime'].apply(time_to_milliseconds)
    fastest_laps_info = res_df_prep.dropna(subset=['fastestLapTime_ms'])
    if fastest_laps_info.empty:
        print("Brak danych o najszybszych okrążeniach w results_df.")
        return
    idx_fastest = fastest_laps_info.groupby('raceId')['fastestLapTime_ms'].idxmin()
    fastest_lap_drivers = fastest_laps_info.loc[idx_fastest, ['raceId', 'driverId']]
    fastest_lap_drivers = fastest_lap_drivers.rename(columns={'driverId': 'fastest_lap_driverId_actual'})

    data = pd.merge(res_df_prep, q_data_to_merge, on=['raceId', 'driverId', 'constructorId'], how='left')
    data = pd.merge(data, races_df[['raceId', 'year', 'circuitId']], on='raceId', how='left')
    data = pd.merge(data, fastest_lap_drivers, on='raceId', how='left')
    data['target_fastest_lap'] = (data['driverId'] == data['fastest_lap_driverId_actual']).astype(int)

    features = ['grid', 'position_qualify', 'best_quali_ms', 'year', 'circuitId', 'constructorId']
    target = 'target_fastest_lap'

    if 'grid' not in data.columns:
        print("Brak kolumny 'grid'.")
        return

    data_cleaned = data.dropna(subset=features + [target])
    if data_cleaned.empty or len(data_cleaned[target].unique()) < 2:
        print("Brak danych po czyszczeniu lub za mało klas.")
        return

    X = data_cleaned[features]
    y = data_cleaned[target]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = RandomForestClassifier(n_estimators=50, random_state=42, class_weight='balanced', max_depth=10)
    print("Trenowanie modelu autora najszybszego okrążenia...")
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    print(f"Dokładność dla predykcji autora najszybszego okrążenia: {accuracy_score(y_test, predictions):.2f}")
    print(classification_report(y_test, predictions, zero_division=0, target_names=['No Fastest Lap', 'Fastest Lap']))

    # --- WIZUALIZACJA I ANALIZA (Zadanie 3) ---
    if not data_cleaned.empty and drivers_df is not None:
        # Liczba najszybszych okrążeń na kierowcę (top 10)
        fl_counts = data_cleaned[data_cleaned['target_fastest_lap'] == 1]['driverId'].value_counts().nlargest(10)
        fl_counts_df = pd.merge(fl_counts.rename('count'), drivers_df[['driverId', 'forename', 'surname']],
                                left_index=True, right_on='driverId')
        fl_counts_df['driver_name'] = fl_counts_df['forename'] + " " + fl_counts_df['surname']

        plt.figure(figsize=(12, 7))
        sns.barplot(x='count', y='driver_name', data=fl_counts_df, palette='viridis')
        plt.title('Top 10 kierowców z największą liczbą najszybszych okrążeń (w danych treningowych)')
        plt.xlabel('Liczba najszybszych okrążeń')
        plt.ylabel('Kierowca')
        plt.tight_layout()
        plt.show()

        # Cechy o największym znaczeniu
        if hasattr(model, 'feature_importances_'):
            importances_fl = pd.Series(model.feature_importances_, index=X_train.columns).sort_values(ascending=False)
            plt.figure(figsize=(10, 6))
            sns.barplot(x=importances_fl.values, y=importances_fl.index)
            plt.title('Ważność cech dla modelu autora najszybszego okrążenia')
            plt.xlabel('Ważność')
            plt.ylabel('Cecha')
            plt.tight_layout()
            plt.show()

    # Przykładowa predykcja dla wyścigu (kod z poprzedniej wersji)
    if not X_test.empty:
        X_test_with_ids = data_cleaned.loc[X_test.index, ['raceId', 'driverId'] + features].copy()
        if not X_test_with_ids.empty and 'raceId' in X_test_with_ids.columns:
            races_in_test = X_test_with_ids[['raceId']].drop_duplicates()
            races_in_test_details = pd.merge(races_in_test, races_df[['raceId', 'year', 'round', 'name']], on='raceId')
            if not races_in_test_details.empty:
                last_race_in_test = races_in_test_details.sort_values(['year', 'round'], ascending=False).iloc[0]
                last_race_id_in_test = last_race_in_test['raceId']
                print(f"\nPrzykładowa predykcja dla wyścigu: {last_race_in_test['name']} ({last_race_in_test['year']})")
                drivers_in_sample_race_features = X_test_with_ids[X_test_with_ids['raceId'] == last_race_id_in_test][
                    features]
                drivers_in_sample_race_ids = X_test_with_ids[X_test_with_ids['raceId'] == last_race_id_in_test][
                    ['driverId']]
                if not drivers_in_sample_race_features.empty:
                    proba_predictions = model.predict_proba(drivers_in_sample_race_features)[:, 1]
                    results_for_race_df = drivers_in_sample_race_ids.copy()
                    results_for_race_df['probability_fastest_lap'] = proba_predictions
                    results_for_race_df = pd.merge(results_for_race_df, drivers_df[['driverId', 'forename', 'surname']],
                                                   on='driverId', how='left')
                    predicted_driver_row = results_for_race_df.loc[
                        results_for_race_df['probability_fastest_lap'].idxmax()]
                    driver_name = f"{predicted_driver_row['forename']} {predicted_driver_row['surname']}"
                    print(
                        f"  Model przewiduje, że {driver_name} (ID: {predicted_driver_row['driverId']}) ma największe szanse na najszybsze okrążenie z prawdopodobieństwem {predicted_driver_row['probability_fastest_lap']:.3f}")
                    print("  Top 3 kandydatów:")
                    top3_fl = results_for_race_df.sort_values('probability_fastest_lap', ascending=False).head(3)
                    for _, row in top3_fl.iterrows():
                        print(f"    - {row['forename']} {row['surname']}: {row['probability_fastest_lap']:.3f}")
    print("-" * 30 + "\n")


# --- 4. Predykcja zwycięzcy Grand Prix Monako 2025 ---
def predict_monaco_2025_winner():
    print("--- Zadanie 4: Predykcja Zwycięzcy GP Monako 2025 ---")
    if results_df is None or qualifying_df is None or races_df is None or circuits_df is None or drivers_df is None or constructors_df is None:
        print("Brak danych. Pomijanie zadania.")
        return

    monaco_circuit = circuits_df[circuits_df['name'].str.contains("Monaco", case=False, na=False)]
    if monaco_circuit.empty:
        print("Nie znaleziono circuitId dla Monako.")
        return
    monaco_circuit_id = monaco_circuit['circuitId'].iloc[0]
    print(f"Znaleziono circuitId dla Monako: {monaco_circuit_id}")

    q_df_prep_monaco = qualifying_df.copy()
    if 'position' in q_df_prep_monaco.columns:
        q_df_prep_monaco = q_df_prep_monaco.rename(columns={'position': 'position_qualify'})
    else:
        q_df_prep_monaco['position_qualify'] = np.nan
    q_data_to_merge_monaco = q_df_prep_monaco[['raceId', 'driverId', 'constructorId', 'position_qualify']]

    data_monaco = pd.merge(results_df, races_df[['raceId', 'year', 'circuitId', 'name']], on='raceId')
    data_monaco = pd.merge(data_monaco, q_data_to_merge_monaco, on=['raceId', 'driverId', 'constructorId'], how='left')
    data_monaco['is_winner'] = (data_monaco['positionOrder'] == 1).astype(int)

    features_monaco = ['grid', 'position_qualify', 'driverId', 'constructorId', 'year', 'circuitId']
    target_monaco = 'is_winner'

    data_cleaned_monaco = data_monaco.dropna(subset=features_monaco + [target_monaco])
    if data_cleaned_monaco.empty or len(data_cleaned_monaco[target_monaco].unique()) < 2:
        print("Brak danych po czyszczeniu lub za mało klas.")
        return

    X_m = data_cleaned_monaco[features_monaco]
    y_m = data_cleaned_monaco[target_monaco]
    X_train_m, X_test_m, y_train_m, y_test_m = train_test_split(X_m, y_m, test_size=0.2, random_state=42, stratify=y_m)

    model_monaco = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced', max_depth=15,
                                          min_samples_leaf=3)
    print("Trenowanie modelu zwycięzcy wyścigu...")
    model_monaco.fit(X_train_m, y_train_m)
    predictions_m = model_monaco.predict(X_test_m)
    print(f"Dokładność modelu zwycięzcy na zbiorze testowym: {accuracy_score(y_test_m, predictions_m):.2f}")
    print(classification_report(y_test_m, predictions_m, zero_division=0, target_names=['Not Winner', 'Winner']))

    # --- WIZUALIZACJA I ANALIZA (Zadanie 4) ---
    if not data_cleaned_monaco.empty and drivers_df is not None and constructors_df is not None:
        # Liczba zwycięstw w Monako dla kierowców (top 5)
        monaco_races_ids = races_df[races_df['circuitId'] == monaco_circuit_id]['raceId']
        monaco_winners = data_cleaned_monaco[
            (data_cleaned_monaco['raceId'].isin(monaco_races_ids)) &
            (data_cleaned_monaco['is_winner'] == 1)
            ]['driverId'].value_counts().nlargest(5)

        if not monaco_winners.empty:
            monaco_winners_df = pd.merge(monaco_winners.rename('wins'), drivers_df[['driverId', 'forename', 'surname']],
                                         left_index=True, right_on='driverId')
            monaco_winners_df['driver_name'] = monaco_winners_df['forename'] + " " + monaco_winners_df['surname']

            plt.figure(figsize=(10, 6))
            sns.barplot(x='wins', y='driver_name', data=monaco_winners_df, palette='mako')
            plt.title('Top 5 kierowców z największą liczbą zwycięstw w Monako (historycznie)')
            plt.xlabel('Liczba zwycięstw w Monako')
            plt.ylabel('Kierowca')
            plt.tight_layout()
            plt.show()
        else:
            print("Brak historycznych danych o zwycięzcach w Monako w przetworzonym zbiorze.")

        # Cechy o największym znaczeniu dla modelu zwycięzcy
        if hasattr(model_monaco, 'feature_importances_'):
            importances_winner = pd.Series(model_monaco.feature_importances_, index=X_train_m.columns).sort_values(
                ascending=False)
            plt.figure(figsize=(10, 6))
            sns.barplot(x=importances_winner.values, y=importances_winner.index)
            plt.title('Ważność cech dla modelu zwycięzcy wyścigu')
            plt.xlabel('Ważność')
            plt.ylabel('Cecha')
            plt.tight_layout()
            plt.show()

    # Predykcja dla Monako 2025
    print("\nPredykcja dla GP Monako 2025:")
    latest_year_in_data = races_df['year'].max()
    drivers_last_season_ids = \
    results_df[results_df['raceId'].isin(races_df[races_df['year'] == latest_year_in_data]['raceId'])][
        'driverId'].unique()
    if len(drivers_last_season_ids) == 0:
        drivers_last_season_ids = drivers_df['driverId'].unique()
    drivers_for_2025_ids = drivers_last_season_ids[:20]
    if len(drivers_for_2025_ids) == 0:
        print("Brak kierowców do symulacji GP Monako 2025.")
        return

    future_race_data_monaco = []
    for i, driver_id_val in enumerate(drivers_for_2025_ids):
        last_race_for_driver = results_df[results_df['driverId'] == driver_id_val].sort_values('raceId',
                                                                                               ascending=False)
        constructor_id_val = constructors_df['constructorId'].sample(1).iloc[0]
        if not last_race_for_driver.empty:
            constructor_id_val = last_race_for_driver['constructorId'].iloc[0]
        sim_quali_pos = i + 1
        future_race_data_monaco.append({
            'grid': i + 1, 'position_qualify': sim_quali_pos, 'driverId': driver_id_val,
            'constructorId': constructor_id_val, 'year': 2025, 'circuitId': monaco_circuit_id
        })

    future_df_monaco = pd.DataFrame(future_race_data_monaco)
    if not future_df_monaco.empty:
        future_df_monaco = future_df_monaco[features_monaco]
        proba_win_2025 = model_monaco.predict_proba(future_df_monaco)[:, 1]
        future_df_monaco['win_probability'] = proba_win_2025
        future_df_monaco = pd.merge(future_df_monaco, drivers_df[['driverId', 'forename', 'surname']], on='driverId',
                                    how='left')

        if not future_df_monaco.empty and 'win_probability' in future_df_monaco.columns:
            predicted_winner_monaco_row = future_df_monaco.loc[future_df_monaco['win_probability'].idxmax()]
            print(f"Przewidywany zwycięzca GP Monako 2025 (na podstawie symulacji):")
            print(
                f"  Kierowca: {predicted_winner_monaco_row['forename']} {predicted_winner_monaco_row['surname']} (ID: {predicted_winner_monaco_row['driverId']})")
            print(f"  Pozycja startowa (symulowana): {predicted_winner_monaco_row['grid']}")
            print(f"  Prawdopodobieństwo wygranej (wg modelu): {predicted_winner_monaco_row['win_probability']:.3f}")

            print("\nTop 5 przewidywań dla GP Monako 2025:")
            top5_monaco = future_df_monaco.sort_values('win_probability', ascending=False).head(5)
            for _, row in top5_monaco.iterrows():
                print(
                    f"  {row['grid']}. {row['forename']} {row['surname']} - Prawdopodobieństwo: {row['win_probability']:.3f}")

            # Wykres prawdopodobieństw dla symulacji Monako 2025
            plt.figure(figsize=(12, 7))
            top10_monaco_pred = future_df_monaco.sort_values('win_probability', ascending=False).head(10)
            top10_monaco_pred['driver_name'] = top10_monaco_pred['forename'] + " " + top10_monaco_pred['surname']
            sns.barplot(x='win_probability', y='driver_name', data=top10_monaco_pred, palette='crest_r')
            plt.title('Przewidywane prawdopodobieństwo zwycięstwa w GP Monako 2025 (Top 10 symulowanych kierowców)')
            plt.xlabel('Prawdopodobieństwo wygranej')
            plt.ylabel('Kierowca (Symulowana poz. startowa w nawiasie)')
            # Dodanie symulowanej pozycji startowej do etykiet osi Y
            labels = [f"{name} (Grid: {grid})" for name, grid in
                      zip(top10_monaco_pred['driver_name'], top10_monaco_pred['grid'])]
            plt.yticks(ticks=range(len(labels)), labels=labels)
            plt.tight_layout()
            plt.show()
        else:
            print("Nie udało się wygenerować predykcji dla Monako 2025 lub brak kolumny 'win_probability'.")
    else:
        print("Nie udało się stworzyć ramki danych dla predykcji Monako 2025.")
    print("-" * 30 + "\n")


# --- Uruchomienie funkcji predykcyjnych ---
if __name__ == "__main__":
    if not os.path.isdir(DATA_DIR):
        print(f"BŁĄD: Folder '{DATA_DIR}' nie istnieje.")
    else:
        predict_future_lap_time()
        predict_pit_stop_duration_decrease()
        predict_fastest_lap_holder()
        predict_monaco_2025_winner()
        print("Zakończono wszystkie zadania predykcyjne.")