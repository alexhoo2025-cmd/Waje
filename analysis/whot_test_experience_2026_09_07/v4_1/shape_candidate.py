"""Candidate geometry correction; replay agreement is not calibration proof."""
def classify(f):
    w,h=f.get('bbox_w',0),f.get('bbox_h',0)
    if min(w,h)<8:return 'unknown'
    fill=f.get('fill',0)
    rc=f.get('row_center',0)/w;cc=f.get('col_center',0)/h
    top,bottom=f.get('top_width',0),f.get('bottom_width',0)
    if fill>.92:return 'square'
    if top<bottom*.58 and bottom>w*.5 and f.get('row_r2',0)>.6:return 'triangle'
    # Old cross branch accepted circular centre/edge profiles before testing fill.
    if .68<fill<.90 and .75<w/h<1.33:return 'circle'
    if .15<fill<.55 and rc<.78 and cc<.78:return 'star'
    if .32<fill<.68 and rc>.8 and cc>.8:return 'cross'
    return 'unknown'
