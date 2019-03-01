import random
import numpy as np


def distance(a, b):
    a = np.array(a)
    b = np.array(b)
    
    if a.ndim == 1 and b.ndim == 1:
        return np.square(a - b).sum(axis=0)
    
    return np.square(a - b).sum(axis=1)

def centroid(points):
    '''
    Return the center of all points
    '''
    return np.mean(points, axis=0)
        
def k_means(points, n=2, max_iter=1000):
    '''
    Apply the K-Means algorithm
    
    Params
    ======
    - points (np.array) : List of n-dimension points, we want to cluster
    - n (int)           : Number of groups we want to form
    '''    
    n_points = points.shape[0]
    
    centroids = np.random.choice(np.arange(points.shape[0]), n, replace=False).tolist()
    
    old_groups = None
    
    for _ in range(max_iter): 
        groups = [[] for _ in range(n)]
        
        # Group each points to the nearest centroid
        for i, p in enumerate(points):
            distances = distance(points[centroids], p)
            cluster = distances.argmin()
            groups[cluster].append(i)
        
        if groups == old_groups:
            return groups
        
        old_groups = groups
        
        # Update centroid
        centroids = []
        for g in groups:
            c = centroid(points[g])
            distances = distance(points, c)
            distances[centroids] = float('inf')
            centroids.append(distances.argmin())
        
    return groups