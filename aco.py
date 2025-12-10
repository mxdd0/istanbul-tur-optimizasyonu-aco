import numpy as np

class AntColonyOptimizer:
    def __init__(self, distances, n_ants, n_best, n_iterations, decay, alpha=1, beta=1):
        """
        ACO Algoritması Parametreleri:
        distances: Mesafe matrisi (şehirler arası uzaklıklar)
        n_ants: Karınca sayısı
        n_best: Her turda feromon bırakacak en iyi karınca sayısı
        n_iterations: Döngü sayısı
        decay: Buharlaşma oranı (0 ile 1 arası)
        alpha: Feromonun önemi
        beta: Mesafenin (görünürlüğün) önemi
        """
        self.distances = distances
        self.pheromone = np.ones(self.distances.shape) / len(distances)
        self.all_inds = range(len(distances))
        self.n_ants = n_ants
        self.n_best = n_best
        self.n_iterations = n_iterations
        self.decay = decay
        self.alpha = alpha
        self.beta = beta

    def run(self):
        shortest_path = None
        all_time_shortest_path = ("placeholder", np.inf)
        history = [] # Grafik için veri tutulur

        for i in range(self.n_iterations):
            all_paths = self.gen_all_paths()
            self.spread_pheronome(all_paths, self.n_best, shortest_path=shortest_path)
            
            # Bu turun en iyisini bul
            shortest_path = min(all_paths, key=lambda x: x[1])
            
            # Genel en iyiyi güncelle
            if shortest_path[1] < all_time_shortest_path[1]:
                all_time_shortest_path = shortest_path
            
            # Feromonu buharlaştır
            self.pheromone * self.decay
            
            history.append(all_time_shortest_path[1])
            
        return all_time_shortest_path, history

    def spread_pheronome(self, all_paths, n_best, shortest_path):
        sorted_paths = sorted(all_paths, key=lambda x: x[1])
        for path, dist in sorted_paths[:n_best]:
            for move in path:
                self.pheromone[move] += 1.0 / self.distances[move]

    def gen_path_dist(self, path):
        total_dist = 0
        for ele in path:
            total_dist += self.distances[ele]
        return total_dist

    def gen_all_paths(self):
        all_paths = []
        for i in range(self.n_ants):
            path = self.gen_path(0)
            all_paths.append((path, self.gen_path_dist(path)))
        return all_paths

    def gen_path(self, start_node):
        path = []
        visited = set()
        visited.add(start_node)
        prev = start_node
        for i in range(len(self.distances) - 1):
            move = self.pick_move(self.pheromone[prev], self.distances[prev], visited)
            path.append((prev, move))
            prev = move
            visited.add(move)
        path.append((prev, start_node)) # Başlangıça dönüş
        return path

    def pick_move(self, pheromone, dist, visited):
        pheromone = np.copy(pheromone)
        pheromone[list(visited)] = 0

        row = pheromone ** self.alpha * (( 1.0 / dist) ** self.beta)
        
        # Olasılık hatalarını düzeltme (sıfıra bölme vb.)
        if row.sum() == 0:
             # Eğer tüm olasılıklar 0 ise rastgele seç (gidilmemişlerden)
             available = [i for i in range(len(dist)) if i not in visited]
             return np.random.choice(available)
             
        norm_row = row / row.sum()
        move = np.random.choice(self.all_inds, 1, p=norm_row)[0]
        return move