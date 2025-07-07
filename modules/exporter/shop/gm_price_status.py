from .shipping import export_shipping

def export_gm_price_status(parameters):
    """
    Exports gm_price_status based on p_shipping value.
    
    Logic:
    - p_shipping = 1, 2, 3, 4, 5 -> gm_price_status = 0 (lieferbar)
    - p_shipping = 6, 7 -> gm_price_status = 2 (nicht lieferbar)
    - p_shipping = 8 -> gm_price_status = 1 (auf Anfrage)
    - Default/unknown values -> gm_price_status = 0
    """

    p_shipping_str = export_shipping(parameters)
    
    if p_shipping_str is None:
        return "0"
    
    try:
        p_shipping_value = int(p_shipping_str)
    except (ValueError, TypeError):
        return "0"
    
    if p_shipping_value in [1, 2, 3, 4, 5]:
        return "0"  # lieferbar
    elif p_shipping_value in [6, 7]:
        return "2"  # nicht lieferbar
    elif p_shipping_value in [8]:
        return "1"  # auf Anfrage
    else:
        return "0"
