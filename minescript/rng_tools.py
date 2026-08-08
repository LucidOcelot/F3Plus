from __future__ import annotations
import math, random
from .seed.java_rng import JavaRandom
from collections import Counter

def probability(successes:int,total:int):
    total=max(1,int(total)); successes=max(0,min(total,int(successes)))
    p=successes/total
    return {'successes':successes,'total':total,'probability':p,'percent':p*100}

def at_least_one(chance:float, attempts:int):
    p=max(0.0,min(1.0,float(chance))); n=max(0,int(attempts))
    r=1-(1-p)**n
    return {'single_chance':p,'attempts':n,'at_least_one':r,'percent':r*100}

def expected_attempts(chance:float):
    p=max(0.0,min(1.0,float(chance)))
    return math.inf if p<=0 else 1/p

def weighted_roll(entries:list[tuple[str,float]], rolls=10000, seed=0):
    rows=[(str(n),float(w)) for n,w in entries if float(w)>0]
    if not rows: return {}
    rng=random.Random(seed); names=[r[0] for r in rows]; weights=[r[1] for r in rows]
    c=Counter(rng.choices(names,weights=weights,k=max(1,int(rolls))))
    return {n:{'count':c[n],'rate':c[n]/max(1,int(rolls))} for n in names}

def sequence(seed:int,count=16,bits=31):
    """Preview the classic java.util.Random LCG sequence from a Java setSeed value."""
    rng=JavaRandom(int(seed)); bits=max(1,min(32,int(bits)))
    if bits==32:
        return [rng.next_int() for _ in range(max(0,int(count)))]
    return [rng.next(bits) for _ in range(max(0,int(count)))]

def lapis_cost(enchantments:int, slot_level=3):
    e=max(0,int(enchantments)); s=max(1,min(3,int(slot_level))); return {'enchantments':e,'lapis':e*s,'xp_levels_spent':e*s}

def bookshelf_power(bookshelves:int):
    b=max(0,min(15,int(bookshelves))); return {'bookshelves':b,'max_table_level':min(30,b*2),'full_power':b>=15}

def grindstone_plan(rerolls:int, dummy_level=1):
    n=max(0,int(rerolls)); return {'rerolls':n,'dummy_enchants':n,'minimum_lapis':n*max(1,int(dummy_level))}

def xp_for_level(level:int):
    l=max(0,int(level))
    if l<=16:return l*l+6*l
    if l<=31:return int(2.5*l*l-40.5*l+360)
    return int(4.5*l*l-162.5*l+2220)

def mob_drop(chance:float,kills:int,looting_bonus=0.0):
    p=max(0,min(1,float(chance)+float(looting_bonus))); k=max(0,int(kills))
    return {'expected_drops':p*k,**at_least_one(p,k)}

def barter(entries:list[tuple[str,float]],ingots:int,seed=0):
    return weighted_roll(entries,max(1,int(ingots)),seed)

def enchant_probability(base_chance:float, rerolls:int=1): return at_least_one(base_chance,rerolls)
