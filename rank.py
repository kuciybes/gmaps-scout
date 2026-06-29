import json, math, csv

LAT0, LON0 = 36.1994705, 29.6397906
RADIUS = 500.0

def hav(la1, lo1, la2, lo2):
    R=6371000.0
    p1,p2=math.radians(la1),math.radians(la2)
    dp=math.radians(la2-la1); dl=math.radians(lo2-lo1)
    a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))

rows=[]
with open("/home/adking/projects/gmaps-scout/out/results.json") as f:
    for line in f:
        line=line.strip()
        if not line: continue
        d=json.loads(line)
        lat=d.get("latitude"); lon=d.get("longitude") or d.get("longtitude")
        if lat is None or lon is None: continue
        dist=hav(LAT0,LON0,lat,lon)
        rows.append({
            "title": d.get("title",""),
            "category": d.get("category","") or "",
            "rating": d.get("review_rating") or 0,
            "reviews": d.get("review_count") or 0,
            "price": d.get("price_range","") or "",
            "dist": round(dist),
            "address": (d.get("address") or "").replace("\n"," "),
            "web": d.get("web_site","") or "",
            "link": d.get("link","") or "",
        })

print(f"Всего спарсено: {len(rows)}")
print(f"review_count>0: {sum(1 for r in rows if r['reviews']>0)}  | макс отзывов: {max((r['reviews'] for r in rows), default=0)}")
inrad=[r for r in rows if r['dist']<=RADIUS]
print(f"В радиусе {int(RADIUS)} м: {len(inrad)}")

# Bayesian weighted score (m = prior count, C = global mean rating among rated places)
rated=[r for r in inrad if r['reviews']>0 and r['rating']>0]
C=sum(r['rating'] for r in rated)/len(rated) if rated else 0
m=20
for r in inrad:
    v=r['reviews']; R=r['rating']
    r['score']=round((v/(v+m))*R + (m/(v+m))*C, 3) if (v>0 and R>0) else 0

# sort by rating desc, then reviews desc
by_rating=sorted(inrad, key=lambda r:(-r['rating'], -r['reviews']))
# smart pick: weighted score desc (only places with some reviews)
by_score=sorted([r for r in inrad if r['reviews']>0], key=lambda r:-r['score'])

def table(rows, n=999):
    print(f"{'#':>2}  {'Рейтинг':>7} {'Отзывы':>7}  {'м':>4}  {'Цена':<7} {'Категория':<22} Название")
    for i,r in enumerate(rows[:n],1):
        print(f"{i:>2}  {r['rating']:>7} {r['reviews']:>7}  {r['dist']:>4}  {r['price']:<7} {r['category'][:22]:<22} {r['title']}")

print("\n================ СОРТ: по рейтингу, затем по числу отзывов ================")
table(by_rating)
print(f"\n(глобальный средний рейтинг в зоне = {round(C,2)}, prior m={m})")
print("\n================ УМНЫЙ ВЫБОР: взвешенный балл (рейтинг × вес отзывов) ================")
print(f"{'#':>2}  {'Балл':>6} {'Рейтинг':>7} {'Отзывы':>7}  {'м':>4}  {'Категория':<22} Название")
for i,r in enumerate(by_score[:15],1):
    print(f"{i:>2}  {r['score']:>6} {r['rating']:>7} {r['reviews']:>7}  {r['dist']:>4}  {r['category'][:22]:<22} {r['title']}")

# write CSV (sorted by rating then reviews)
with open("/home/adking/projects/gmaps-scout/out/restaurants_500m.csv","w",newline="") as f:
    w=csv.writer(f)
    w.writerow(["rank","rating","reviews","weighted_score","dist_m","price","category","title","address","web","maps_link"])
    for i,r in enumerate(by_rating,1):
        w.writerow([i,r['rating'],r['reviews'],r['score'],r['dist'],r['price'],r['category'],r['title'],r['address'],r['web'],r['link']])
print("\nCSV: out/restaurants_500m.csv")
