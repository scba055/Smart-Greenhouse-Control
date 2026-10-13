import random
import numpy as np
import pandas as pd
import os
from datetime import datetime

class GAController:
    def __init__(self, data, RF_model):
        self.data = data.copy()
        self.rf_model = RF_model
        
        # GA parameters - changed these to better suit my laptop's specs instead of accounting for the rpi's limited resources
        self.population_size = 50
        self.generations = 80
        self.mutation_rate = 0.2
        # optimal pH range
        self.optimal_lower = 5.8
        self.optimal_upper = 6.8
        
    # create random individual 
    def create_individual(self):
        lower_trigger = random.uniform(5.80, 6.05)
        upper_trigger = random.uniform(6.15, 6.40)
        cooldown_time = random.randint(40, 60)
        
        return [
            lower_trigger,
            upper_trigger,
            cooldown_time
        ]
    
    # evaluate fitness of an individual GA solution    
    def fitness(self, individual):
        lower_trigger, upper_trigger, cooldown_time = individual
        
        predicted_ph_values = (
            self.data["Predicted_pH"].dropna().values
        )
        
        # return 0 if there's no pH data to evaluate against
        if len(predicted_ph_values) == 0:
            return 0
        
        # time outside optimal range
        outside_range_penalty = 0
        
        # adding a more severe penalty to prevent the pH from going out of range
        for ph in predicted_ph_values:

            if ph < self.optimal_lower:

                deviation = self.optimal_lower - ph

                # moderate linear penalty
                outside_range_penalty += deviation * 5

                # soft quadratic unsafe penalty
                if ph < 5.5:
                    outside_range_penalty += (
                        (5.5 - ph) ** 2
                    ) * 20

            elif ph > self.optimal_upper:

                deviation = ph - self.optimal_upper

                outside_range_penalty += deviation * 5

                if ph > 7.2:
                    outside_range_penalty += (
                        (ph - 7.2) ** 2
                    ) * 20
        
        # oscillation penalty, penalise if pH crosses triggers too often
        threshold_gap = upper_trigger - lower_trigger
        oscillation_penalty = 0
        
        # clamping the penalty to avoid a negative oscillation penalty
        if threshold_gap < 0.15:
            oscillation_penalty = max(
                0,
                10 * (0.15 - threshold_gap)
            )
            
        # final fitness score (lower is better)
        fitness_score = (
            outside_range_penalty +
            oscillation_penalty
        )
        
        return fitness_score
    
    # parent selection
    def select_parents(self, population):

        fitness_scores = [
            self.fitness(ind)
            for ind in population
        ]

        # Inverse fitness because LOWER is better
        selection_probs = [
            1 / (score + 1e-6)
            for score in fitness_scores
        ]

        # Normalize probabilities
        total = sum(selection_probs)

        selection_probs = [
            p / total
            for p in selection_probs
        ]

        return random.choices(
            population,
            weights=selection_probs,
            k=2
        )
    
    # crossover between two parents to create a child
    def crossover(self, parent1, parent2):
        child = [
            random.choice([
                parent1[0], parent2[0]
            ]),
            random.choice([
                parent1[1], parent2[1]
            ]),
            random.choice([
                parent1[2], parent2[2]
            ])
        ]
        
        return child
    
    # mutation of a child solution
    def mutate(self, individual):
        # lower trigger mutation
        if random.random() < self.mutation_rate:
            individual[0] += random.uniform(-0.05, 0.05)
            individual[0] = max(5.80, min(6.05, individual[0]))

        # upper trigger mutation
        if random.random() < self.mutation_rate:
            individual[1] += random.uniform(-0.05, 0.05)
            individual[1] = max(6.15, min(6.40, individual[1]))
        
        # cooldown mutation
        if random.random() < self.mutation_rate:
            individual[2] += random.randint(-10, 10)
            individual[2] = max(40, min(70, individual[2]))
        
        return individual
    
    # main evolution loop
    def run(self):
    
        # initialize population
        population = [
            self.create_individual()
            for _ in range(self.population_size)
        ]
        
        best_solution = None
        best_fitness = float("inf")
        
        elite_count = 1
        history = [] # allows me to track best fitness with each run through of the GA
        run_id = datetime.now().strftime(
            "%Y%m%d_%H:%M:%S"
        )
        
        for gen in range(self.generations):
            
            # progress update
            print(f"Starting generation {gen+1}")
            
            # sort population by fitness (lower is better)
            population = sorted(
                population,
                key=lambda x: self.fitness(x)
            )
            
            current_best = population[0]
            current_fitness = self.fitness(current_best)
            
            avg_fitness = np.mean(
                [self.fitness(ind) for ind in population]
            )

            history.append({
                "Run_ID": run_id,
                "Timestamp": datetime.now(),
                "Generation": gen + 1,
                "Best_Fitness": current_fitness,
                "Average_Fitness": avg_fitness,
                "Lower_Trigger": current_best[0],
                "Upper_Trigger": current_best[1],
                "Cooldown_Time": current_best[2]
            })
            
            # update global best solution
            if current_fitness < best_fitness:
                best_fitness = current_fitness
                best_solution = current_best
            
            # preserve top individuals
            new_population = population[:elite_count]
            
            # generate offspring
            while len(new_population) < self.population_size:
                
                parent1, parent2 = self.select_parents(population)
                
                child = self.crossover(parent1, parent2)
                child = self.mutate(child)
                
                new_population.append(child)
            
            # replace old population
            population = new_population
            
            print(
                f"Generation {gen+1}: "
                f"Best Fitness = {best_fitness:.4f} | "
                f"Best Solution = {best_solution}"
            )
            
        history_df = pd.DataFrame(history)

        database_file = "ga_experiment_database.csv"

        if os.path.exists(database_file):

            history_df.to_csv(
                database_file,
                mode="a",
                header=False,
                index=False
            )

        else:

            history_df.to_csv(
                database_file,
                index=False
            )

        print("[GA] Experimental data appended.")
            
        return best_solution    
    
    # run the GA and return the best solution
    def optimize(self):
        import json
        from ML_Controller import MLController # grabs the RF model from the ML controller
        
        df = pd.read_csv("Greenhouse_Processed.csv")
        
        # ensure pH is numeric
        df["SEEED_PH"] = pd.to_numeric(
            df["SEEED_PH"],
            errors="coerce"
        )
        
        # trains the RF model on the dataset
        ml = MLController()
        ml.train(df)
        
        feature_columns = ml.feature_columns
        X = df[feature_columns]
        df["Predicted_pH"] = ml.ph_model.predict(X)
        
        # creates GA
        ga = GAController(
            df,
            ml.ph_model
        )
        
        # runs GA
        best_solution = ga.run()
        
        # saves best solution parameters to JSON for use in RPI controller
        params = {
            "lower_trigger": best_solution[0],
            "upper_trigger": best_solution[1],
            "cooldown_time": best_solution[2]
        } 
        
        # Save parameters to a JSON file
        with open("ga_params.json", "w") as f:
            json.dump(params, f, indent=4)
            
        print("[GA] Parameters saved.")
        
        print("\n Best GA Solution Found:")
        print(best_solution)
        
        return best_solution
    
    
# allows me to run the GA controller directly for testing purposes    
if __name__ == "__main__":
    controller = GAController(
        pd.DataFrame(), # placeholder, will be loaded in optimize()
        None # placeholder, will be trained in optimize()
    )
    controller.optimize()