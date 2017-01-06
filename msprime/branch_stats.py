import msprime


def path_length(tr,x,y):
    L = 0
    mrca = tr.mrca(x,y)
    for u in x,y:
        while u != mrca:
            L += tr.branch_length(u)
            u = tr.parent(u)
    return L

def branch_length_diversity(ts,x,y):
    S = 0
    for tr in ts.trees():
        S += path_length(tr,x,y)*tr.length
    return S/ts.sequence_length

def branch_length_Y(ts,x,y,z):
    S = 0
    for tr in ts.trees():
        xy_mrca = tr.mrca(x,y)
        xz_mrca = tr.mrca(x,z)
        yz_mrca = tr.mrca(y,z)
        if xy_mrca == xz_mrca:
            #   /\
            #  / /\
            # x y  z
            S += path_length(tr,x,yz_mrca)*tr.length
        elif xy_mrca == yz_mrca:
            #   /\
            #  / /\
            # y x  z
            S += path_length(tr,x,xz_mrca)*tr.length
        elif xz_mrca == yz_mrca:
            #   /\
            #  / /\
            # z x  y
            S += path_length(tr,x,xy_mrca)*tr.length
    return S/ts.sequence_length


def branch_stats_node_iter(ts,leaf_sets,condition,method='length'):
    '''
    Here leaf_sets is a list of lists of leaves, and condition is a function
    whose argument is a list of integers of the same length as leaf_sets
    that returns a boolean.  A branch in a tree is *counted* if condition(x)
    is True, where x[i] is the number of leaves in leaf_sets[i] below that
    branch.  This finds the sum of all counted branches for each tree,
    and averages this across the tree sequence ts, weighted by genomic length.

    If method='mutations' instead, then branch lengths will be measured in
    numbers of mutations instead of time.

    This version is inefficient as it iterates over all nodes in each tree.
    '''
    tr_its = [ ts.trees(tracked_leaves=x,leaf_counts=True,leaf_lists=True) for x in leaf_sets ]
    S = 0
    for k in range(ts.num_trees):
        trs = [ next(x) for x in tr_its ]
        root = trs[0].root
        tr_len = trs[0].length
        if method=='length':
            for node in trs[0].nodes():
                if node is not root:
                    x = [ tr.num_tracked_leaves(node) for tr in trs ]
                    # print(node,x,condition(x),trs[0].branch_length(node),tr_len)
                    if condition(x):
                        S += trs[0].branch_length(node) * tr_len
        elif method=='mutations':
            count_nodes = dict([ 
                (node,condition([ tr.num_tracked_leaves(node) for tr in trs ])) 
                for node in trs[0].nodes() if node is not root ])
            # print(count_nodes)
            for mut in trs[0].mutations():
                # print(mut)
                if count_nodes[mut.node]:
                    S += 1
        else:
            raise(TypeError("Unknown method "+method))
    S /= ts.get_sequence_length()
    return S

def branch_stats(ts,leaf_sets,condition,method='length'):
    '''
    Here leaf_sets is a list of lists of leaves, and condition is a function
    whose argument is a list of integers of the same length as leaf_sets
    that returns a boolean.  A branch in a tree is *counted* if condition(x)
    is True, where x[i] is the number of leaves in leaf_sets[i] below that
    branch.  This finds the sum of all counted branches for each tree,
    and averages this across the tree sequence ts, weighted by genomic length.

    Doesn't do method='mutations'.
    '''
    # initialize
    num_leaf_sets = len(leaf_sets)
    S = 0.0
    L = 0.0
    N = ts.num_nodes
    X = [ [ int(u in a) for a in leaf_sets] for u in range(N) ]
    # we will essentially construct the tree
    pi = [-1 for j in range(N)]
    node_time = [0.0 for u in range(N)]
    for length,records_out,records_in in ts.diffs():
        for node,children,time in records_out:
            # print("Out: ",node,children,time)
            # print("\t",X, "-->", L)
            for child in children:
                if condition(X[child]):
                    L -= (node_time[pi[child]] - node_time[child])
                    # print("\t\tchild:",child,L)
                pi[child] = -1
            if pi[node] != -1 and condition(X[node]):
                L -= (node_time[pi[node]] - node_time[node])
                # print("\t\tnode:",node,L)
            # propagate change up the tree
            u = pi[node]
            if u != -1:
                next_u = pi[u]
                while u != -1:
                    old_f = condition(X[u])
                    for k in range(num_leaf_sets):
                        X[u][k] -= X[node][k]
                    new_f = condition(X[u])
                    # need to update X for the root,
                    # but the root does not have a branch length
                    if next_u != -1:
                        if old_f and not new_f:
                            L -= (node_time[pi[u]] - node_time[u])
                            # print("\t\tanc-:",u,L)
                        if new_f and not old_f:
                            L += (node_time[pi[u]] - node_time[u])
                            # print("\t\tanc+:",u,L)
                    u = next_u
                    next_u = pi[next_u]
            for k in range(num_leaf_sets):
                X[node][k] = 0
            # print("\t",X, "-->", L)
        for node,children,time in records_in:
            # print("In: ",node,children,time)
            # print("\t",X, "-->", L)
            dx = [0 for a in leaf_sets]
            node_time[node] = time
            for child in children:
                if condition(X[child]):
                    L += node_time[node] - node_time[child]
                    # print("\t\tchild:",child,L)
                pi[child] = node
                for k in range(num_leaf_sets):
                    dx[k] += X[child][k]
            for k in range(num_leaf_sets):
                X[node][k] = dx[k]
            if pi[node] != -1 and condition(X[node]):
                L += node_time[pi[node]] - node_time[node]
                # print("\t\tnode:",node,L)
            # propagate change up the tree
            u = pi[node]
            if u != -1:
                next_u = pi[u]
                while u != -1:
                    # print("\t\t\tu:",u,next_u)
                    old_f = condition(X[u])
                    for k in range(num_leaf_sets):
                        X[u][k] += dx[k]
                    new_f = condition(X[u])
                    # need to update X for the root,
                    # but the root does not have a branch length
                    if next_u != -1:
                        if old_f and not new_f:
                            L -= (node_time[pi[u]] - node_time[u])
                            # print("\t\tanc-:",u,L)
                        if new_f and not old_f:
                            L += (node_time[pi[u]] - node_time[u])
                            # print("\t\tanc+:",u,L)
                    u = next_u
                    next_u = pi[next_u]
            # print("\t",X, "-->", L)
        # print("next tree:",L,length)
        S += L * length
    S /= ts.get_sequence_length()
    return S

