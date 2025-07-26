def provide_feedback(metrics):
    feedback = []
    
    # Feedback sulla distanza e durata
    feedback.append(f"Hai percorso {metrics['distance_km']:.2f} km in {metrics['duration_sec'] / 60:.2f} minuti.")
    
    # Feedback sulla frequenza cardiaca
    if metrics['average_heart_rate'] > 150:  # Soglia di esempio
        feedback.append("Attenzione: la tua frequenza cardiaca media è alta. Assicurati di recuperare adeguatamente.")
    elif metrics['average_heart_rate'] < 100:
        feedback.append("La tua frequenza cardiaca media è bassa. Potresti aumentare l'intensità dei tuoi allenamenti.")
    
    # Feedback sulla velocità
    if metrics['speed_avg_kmh'] < 8:  # Soglia di esempio
        feedback.append("La tua velocità media è bassa. Considera di lavorare sulla tua resistenza.")
    else:
        feedback.append("Ottimo lavoro! La tua velocità media è buona.")
    
    # Feedback sul passo
    if metrics['pace_min_per_km'] > 6:  # Soglia di esempio
        feedback.append("Il tuo passo medio è un po' lento. Prova a migliorare la tua velocità.")
    else:
        feedback.append("Il tuo passo medio è eccellente!")
    
    return feedback

# Esempio di utilizzo
feedback = provide_feedback(metrics)

# Stampa il feedback
print("\nFeedback:")
for line in feedback:
    print(line)



