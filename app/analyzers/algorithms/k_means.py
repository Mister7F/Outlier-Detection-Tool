import random
import numpy as np

def distance(a, b):
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
    
    # List of centroid indexe in points
    centroids = random.sample(range(n_points),  n)
    
    # List of index lists
    groups = [ [c] for c in centroids ]
    old_group = None
    
    for _ in range(max_iter):
        
        # Update centroid
        centroids = []
        for g in groups:        
            d = distance(points, centroid(g))        
            d[centroids] = float('inf')        
            centroids.append(d.argmin())
        groups = [ [c] for c in centroids ]
        
        # Group each points to the nearest centroid
        for i, point in enumerate(points):

            if i in centroids:
                continue

            groups[distance(point, points[centroids]).argmin()].append(i)
        
        # The groups have not changed
        if old_group == groups:
            break
               
        old_group = groups
        
    return groups
