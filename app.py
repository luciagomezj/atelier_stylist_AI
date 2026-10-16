import json
from pathlib import Path
import pandas as pd
import streamlit as st
from stylist import generate,chat,three_looks
from database import init,record,favorite,favorites,analytics

st.set_page_config(page_title='ATELIER AI | Personal Stylist',page_icon='✦',layout='wide')
st.markdown('''<style>
.stApp{background:#faf8f5;color:#282421}.block-container{max-width:1450px;padding-top:2rem}
h1,h2,h3{font-family:Georgia,serif}div.stButton>button[kind="primary"]{background:#282421;color:white;border:0}
[data-testid="stMetric"]{background:white;border:1px solid #e5ded5;border-radius:12px;padding:16px} [data-testid="stImage"] img{border-radius:14px;object-fit:cover} div[data-testid="stVerticalBlockBorderWrapper"]{border-radius:16px}
</style>''',unsafe_allow_html=True)
init()
@st.cache_data
def catalog(): return pd.read_csv('catalog.csv')
df=catalog()
for key,default in {'look':None,'prefs':None,'excluded':[],'messages':[],'compare':[],'variants':[]}.items():
    if key not in st.session_state: st.session_state[key]=default

st.caption('ATELIER AI   /   PERSONAL STYLING STUDIO')
st.title('Your style. Reimagined.')
st.write('A curated wardrobe, personalized with local generative AI.')
st.divider()
t1,t2,t3,t4=st.tabs(['✦ Personal Stylist','Collection','Saved Looks','Business Insights'])

def item_card(item):
    # Priority: local licensed photos (JPG/PNG/WEBP), then optional
    # external image URL, then the included demo illustration.
    pid = int(item['id'])
    image = None
    for ext in ('jpg', 'jpeg', 'webp', 'png'):
        candidate = Path('photos') / f'{pid}.{ext}'
        if candidate.is_file():
            image = str(candidate)
            break
    if image is None and 'image_url' in item.index:
        url = str(item['image_url']).strip()
        if url.startswith(('https://', 'http://')):
            image = url
    if image is None:
        fallback = Path('images') / f'{pid}.png'
        if fallback.is_file():
            image = str(fallback)
    if image:
        try:
            st.image(image, use_container_width=True)
        except Exception:
            st.info('Photo unavailable')
    else:
        st.info('Photo coming soon')
    st.markdown(f"**{item['name']}**")
    st.caption(f"{item['color'].title()} · {item['category'].title()}")
    st.write(f"€{float(item['price']):.2f}")
    if 'product_url' in item.index:
        link = str(item['product_url']).strip()
        if link.startswith(('https://', 'http://')):
            st.link_button('View product ↗', link, use_container_width=True)

with t1:
    left,right=st.columns([1,2],gap='large')
    with left:
        st.subheader('Tell us about your look')
        occasion=st.selectbox('Occasion',['university','interview','dinner'])
        style=st.selectbox('Style',['casual','classic','elegant','streetwear'])
        color=st.selectbox('Preferred color',['Any','black','white','beige','blue','grey','brown','navy','gold'])
        season=st.selectbox('Season',['Any','Spring','Summer','Autumn','Winter'])
        budget=st.slider('Maximum budget (€)',50,300,150,5)
        avoid=st.text_input('Avoid (comma-separated)','',placeholder='heels, black, hoodie')
        notes=st.text_area('Anything else?',placeholder='Comfortable and minimal, no heels...')
        extras=st.checkbox('Include jacket and accessories when possible',value=True)
        go=st.button('Create my outfit ✦',type='primary',use_container_width=True)
    prefs=(occasion,style,color,season,budget,avoid,notes,extras)
    if st.session_state.prefs!=prefs:
        st.session_state.prefs=prefs;st.session_state.look=None;st.session_state.excluded=[];st.session_state.messages=[];st.session_state.variants=[]
    if go:
        st.session_state.excluded=[]
        try:
            with st.spinner('Qwen is styling your look...'):
                st.session_state.variants=three_looks(df,occasion,style,budget,color,avoid,season,extras)
                if not st.session_state.variants:
                    raise ValueError('No compatible outfits for this budget and occasion.')
                look=generate(df,occasion,style,budget,color,avoid,season=season,extras=extras,notes=notes,selected_ids=st.session_state.variants[1 if len(st.session_state.variants)>1 else 0]['ids'])
            st.session_state.look=look
            record(occasion,style,budget,look[1])
        except Exception as e: st.error(f'Could not generate: {e}')
    with right:
        st.subheader('Your personalized edit')
        if st.session_state.variants:
            st.markdown('#### Explore three outfit options')
            variant_cols=st.columns(len(st.session_state.variants))
            for i,(col,variant) in enumerate(zip(variant_cols,st.session_state.variants)):
                with col:
                    st.markdown(f"**{variant['label']}** · €{variant['total']:.2f}")
                    if st.button('Choose this look',key=f'variant_{i}',use_container_width=True):
                        try:
                            with st.spinner('Qwen is styling your look...'):
                                st.session_state.look=generate(df,occasion,style,budget,color,avoid,
                                    season=season,extras=extras,notes=notes,selected_ids=variant['ids'])
                            record(occasion,style,budget,st.session_state.look[1])
                            st.rerun()
                        except Exception as e: st.error(f'Could not load look: {e}')
        if st.session_state.look:
            items,total,explanation=st.session_state.look
            cols=st.columns(3)
            for i,(_,item) in enumerate(items.iterrows()):
                with cols[i%3]: item_card(item)
            st.metric('Total outfit price',f'€{total:.2f}')
            st.caption(f'€{budget-total:.2f} remaining in budget')
            st.markdown('**Why this works**')
            st.write(explanation)
            a,b=st.columns(2)
            with a:
                if st.button('♡ Save look',use_container_width=True):
                    favorite([int(x) for x in items.id],explanation);st.success('Saved!')
            with b:
                if st.button('＋ Add to comparison',use_container_width=True):
                    st.session_state.compare.append(([int(x) for x in items.id],total));st.success('Added to comparison')
            st.markdown('**Replace a garment**')
            replace=st.selectbox('Choose item',items.name.tolist())
            if st.button('Find alternative'):
                old=int(items[items.name==replace].iloc[0].id)
                locked=[int(x) for x in items[items.id!=old].id if items[items.id==x].iloc[0].category in ('top','bottom','shoes')]
                try:
                    with st.spinner('Finding another option...'):
                        new=generate(df,occasion,style,budget,color,avoid,locked,st.session_state.excluded+[old],season,extras,notes)
                    st.session_state.excluded.append(old);st.session_state.look=new
                    record(occasion,style,budget,new[1]);st.rerun()
                except Exception as e: st.warning(f'No alternative available: {e}')
            st.divider()
            st.markdown('**Ask your AI stylist**')
            for m in st.session_state.messages:
                with st.chat_message(m['role']): st.write(m['content'])
            question=st.chat_input('How could I style this for colder weather?')
            if question:
                st.session_state.messages.append({'role':'user','content':question})
                try:
                    answer=chat(question,items)
                    st.session_state.messages.append({'role':'assistant','content':answer})
                except Exception as e: st.session_state.messages.append({'role':'assistant','content':f'Connection error: {e}'})
                st.rerun()
        else: st.info('Choose your preferences and create your first outfit.')
    if st.session_state.compare:
        st.divider();st.subheader('Compare looks')
        for i,(ids,price) in enumerate(st.session_state.compare,1):
            names=', '.join(df[df.id.isin(ids)].name.tolist())
            st.write(f'**Look {i} · €{price:.2f}:** {names}')
        if st.button('Clear comparison'): st.session_state.compare=[];st.rerun()

with t2:
    st.subheader('Explore the collection')
    category=st.selectbox('Filter category',['All']+sorted(df.category.unique().tolist()))
    subset=df if category=='All' else df[df.category==category]
    for start in range(0,len(subset),4):
        cols=st.columns(4)
        for col,(_,item) in zip(cols,subset.iloc[start:start+4].iterrows()):
            with col: item_card(item)
    st.caption('Demo catalog with AI-generated product imagery and illustrative prices. Not linked to real merchandise.')

with t3:
    st.subheader('Saved looks')
    saved=favorites()
    if not saved: st.info('No saved looks yet.')
    for ids,explanation,date in saved:
        subset=df[df.id.isin(json.loads(ids))]
        st.write(f'**{date[:10]}** — '+', '.join(subset.name.tolist()))
        st.caption(explanation);st.divider()

with t4:
    st.subheader('Business intelligence')
    totals,styles,occasions=analytics()
    c1,c2,c3=st.columns(3)
    c1.metric('Recommendations',totals[0]);c2.metric('Avg. outfit value',f'€{totals[1] or 0:.2f}');c3.metric('Avg. budget',f'€{totals[2] or 0:.2f}')
    a,b=st.columns(2)
    with a:
        st.markdown('**Styles requested**')
        if styles: st.bar_chart(pd.DataFrame(styles,columns=['Style','Count']).set_index('Style'))
    with b:
        st.markdown('**Occasions requested**')
        if occasions: st.bar_chart(pd.DataFrame(occasions,columns=['Occasion','Count']).set_index('Occasion'))
    st.caption('Demo usage metrics, not purchases or conversion rates. No personal user identifiers are collected.')
