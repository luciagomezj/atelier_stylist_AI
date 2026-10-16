import json
from itertools import product
import requests
from pydantic import BaseModel, Field

MODEL = 'qwen3:1.7b'
API = 'http://localhost:11434/api/generate'

class Choice(BaseModel):
    option: int = Field(ge=1)
    explanation: str

def candidates(df, occasion, style, budget, color='Any', avoid='', locked=None,
               excluded=None, season='Any', extras=True):
    """Create valid combinations before asking the language model."""
    locked = set(locked or [])
    excluded = set(excluded or [])
    d = df[~df.id.isin(excluded)].copy()
    # Interview outfits must contain interview-appropriate core garments.
    if occasion == 'interview':
        d = d[(d.occasion == 'interview') | (d.category == 'accessory')].copy()
    forbidden = [w.strip().lower() for w in avoid.split(',') if w.strip()]
    for word in forbidden:
        d = d[~d.name.str.lower().str.contains(word, regex=False)
              & ~d.color.str.lower().str.contains(word, regex=False)]
    groups = [d[d.category == cat].to_dict('records')
              for cat in ('top', 'bottom', 'shoes')]
    if any(not group for group in groups):
        return []
    ranked = []
    for trio in product(*groups):
        ids = {int(x['id']) for x in trio}
        if not locked.issubset(ids):
            continue
        price = sum(float(x['price']) for x in trio)
        if price > budget:
            continue
        score = sum(7 * (x['occasion'] == occasion)
                    + 4 * (x['style'] == style)
                    + 2 * (color != 'Any' and x['color'] == color)
                    for x in trio)
        ranked.append((score, price, list(trio)))
    ranked.sort(key=lambda x: (-x[0], x[1]))
    results = []
    for score, price, trio in ranked:
        chosen = list(trio)
        if extras:
            pool = d[d.category.isin(['outerwear', 'accessory'])].to_dict('records')
            pool.sort(key=lambda x: -(7 * (x['occasion'] == occasion)
                                      + 4 * (x['style'] == style)))
            for item in pool:
                # Extras must match the occasion; no casual hoodie for interviews.
                if item['occasion'] != occasion:
                    continue
                if price + float(item['price']) <= budget and len(chosen) < 5:
                    chosen.append(item)
                    price += float(item['price'])
        ids = [int(x['id']) for x in chosen]
        if not any(o['ids'] == ids for o in results):
            results.append({'ids': ids, 'total': round(price, 2), 'score': score})
        if len(results) >= 80:
            break
    return results


def three_looks(df, occasion, style, budget, color='Any', avoid='',
                season='Any', extras=True):
    """Three different affordable outfit combinations, when available."""
    options = candidates(df, occasion, style, budget, color, avoid,
                         season=season, extras=extras)
    if not options:
        return []
    ordered = sorted(options, key=lambda o: (o['total'], -o['score']))
    picked = [ordered[0]]
    # Middle: strong style match, while different from the cheapest.
    others = [o for o in options if o['ids'] != picked[0]['ids']]
    if others:
        picked.append(others[0])
    # Premium: most expensive distinct outfit within the user's budget.
    others = [o for o in reversed(ordered)
              if all(o['ids'] != x['ids'] for x in picked)]
    if others:
        picked.append(others[0])
    labels = ['Budget', 'Balanced', 'Premium'][:len(picked)]
    return [{**o, 'label': label} for label, o in zip(labels, picked)]


def generate(df, occasion, style, budget, color='Any', avoid='', locked=None,
             excluded=None, season='Any', extras=True, notes='', selected_ids=None):
    options = candidates(df, occasion, style, budget, color, avoid, locked,
                         excluded, season, extras)
    if not options:
        raise ValueError('No hay un conjunto compatible con estos filtros y presupuesto.')
    if selected_ids is not None:
        wanted = set(selected_ids)
        matching = [o for o in options if set(o['ids']) == wanted]
        if not matching:
            raise ValueError('Este look ya no cumple los filtros actuales.')
        options = matching
    prompt = f"""You are a careful fashion stylist. Choose the best PREVALIDATED option.
Occasion={occasion}; style={style}; preferred color={color}; season={season}; notes={notes}.
Never invent products, colors or prices. The color is a preference, not a guarantee.
Return ONLY JSON with option (1-based integer) and explanation (two concise Spanish sentences).
Options: {json.dumps([{'option': i+1, 'total': o['total'], 'items': df[df.id.isin(o['ids'])][['name','color','category']].to_dict('records')} for i,o in enumerate(options[:8])])}"""
    try:
        r = requests.post(API, json={'model': MODEL, 'prompt': prompt,
                          'stream': False, 'format': 'json', 'think': False,
                          'options': {'temperature': 0.2}}, timeout=180)
        r.raise_for_status()
        choice = Choice.model_validate_json(r.json()['response'])
        idx = choice.option - 1
        if idx not in range(min(len(options), 8)):
            raise ValueError('Invalid option')
        explanation = choice.explanation
    except (requests.RequestException, ValueError, KeyError) as e:
        if isinstance(e, requests.RequestException):
            raise
        idx = 0
        explanation = ('Look seleccionado según ocasión, estilo y presupuesto. '
                       'Puedes comparar alternativas o cambiar una prenda.')
    o = options[idx]
    return df[df.id.isin(o['ids'])].copy(), o['total'], explanation

def chat(message,items):
    prompt=f'''You are a friendly fashion advisor. Reply in Spanish, briefly, with concrete styling advice. Current outfit: {items[['name','color','category']].to_json(orient='records')}. User says: {message}. Do not pretend to modify the actual catalog or outfit. If user wants a new selection, tell them to adjust filters and click Generate.'''
    r=requests.post(API,json={'model':MODEL,'prompt':prompt,'stream':False,'think':False},timeout=180)
    r.raise_for_status()
    return r.json()['response'].strip()
