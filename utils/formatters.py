"""
Utilidades de formateo para el Sistema de Ventas y Costos
"""
from decimal import Decimal
from datetime import datetime, date
from config.settings import TAX_CONFIG

class CurrencyFormatter:
    """Formateador de moneda"""
    
    @staticmethod
    def format_currency(amount, include_symbol=True):
        """
        Formatear un monto como moneda
        
        Args:
            amount (Decimal|float|int): Monto a formatear
            include_symbol (bool): Incluir símbolo de moneda
            
        Returns:
            str: Monto formateado
        """
        if amount is None:
            return "$ 0.00" if include_symbol else "0.00"
        
        try:
            decimal_amount = Decimal(str(amount))
            formatted = f"{decimal_amount:,.2f}"
            
            if include_symbol:
                return f"{TAX_CONFIG['currency_symbol']} {formatted}"
            return formatted
        except (ValueError, TypeError):
            return "$ 0.00" if include_symbol else "0.00"
    
    @staticmethod
    def parse_currency(currency_string):
        """
        Parsear una cadena de moneda a Decimal
        
        Args:
            currency_string (str): Cadena de moneda
            
        Returns:
            Decimal: Valor decimal
        """
        if not currency_string:
            return Decimal('0.00')
        
        # Remover símbolo de moneda y espacios
        clean_string = currency_string.replace(TAX_CONFIG['currency_symbol'], '').strip()
        # Remover comas de separadores de miles
        clean_string = clean_string.replace(',', '')
        
        try:
            return Decimal(clean_string)
        except (ValueError, TypeError):
            return Decimal('0.00')

class DateFormatter:
    """Formateador de fechas"""
    
    @staticmethod
    def format_date(date_obj, format_string='%d/%m/%Y'):
        """
        Formatear una fecha
        
        Args:
            date_obj (datetime|date|str): Fecha a formatear
            format_string (str): Formato de salida
            
        Returns:
            str: Fecha formateada
        """
        if date_obj is None:
            return ""
        
        if isinstance(date_obj, str):
            try:
                # Intentar parsear diferentes formatos
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']:
                    try:
                        date_obj = datetime.strptime(date_obj, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return date_obj  # Retornar string original si no se puede parsear
            except:
                return date_obj
        
        if isinstance(date_obj, (datetime, date)):
            return date_obj.strftime(format_string)
        
        return str(date_obj)
    
    @staticmethod
    def format_datetime(datetime_obj, format_string='%d/%m/%Y %H:%M'):
        """
        Formatear una fecha y hora
        
        Args:
            datetime_obj (datetime|str): Fecha y hora a formatear
            format_string (str): Formato de salida
            
        Returns:
            str: Fecha y hora formateada
        """
        return DateFormatter.format_date(datetime_obj, format_string)
    
    @staticmethod
    def parse_date(date_string, format_string='%d/%m/%Y'):
        """
        Parsear una cadena de fecha
        
        Args:
            date_string (str): Cadena de fecha
            format_string (str): Formato esperado
            
        Returns:
            datetime: Objeto datetime
        """
        if not date_string:
            return None
        
        try:
            return datetime.strptime(date_string, format_string)
        except ValueError:
            # Intentar otros formatos comunes
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
                try:
                    return datetime.strptime(date_string, fmt)
                except ValueError:
                    continue
            return None

class NumberFormatter:
    """Formateador de números"""
    
    @staticmethod
    def format_decimal(number, decimal_places=2):
        """
        Formatear un número decimal
        
        Args:
            number (Decimal|float|int): Número a formatear
            decimal_places (int): Número de decimales
            
        Returns:
            str: Número formateado
        """
        if number is None:
            return "0.00"
        
        try:
            decimal_number = Decimal(str(number))
            format_string = f"{{:,.{decimal_places}f}}"
            return format_string.format(float(decimal_number))
        except (ValueError, TypeError):
            return "0.00"
    
    @staticmethod
    def format_percentage(number, decimal_places=2):
        """
        Formatear un número como porcentaje
        
        Args:
            number (Decimal|float|int): Número a formatear (0.19 = 19%)
            decimal_places (int): Número de decimales
            
        Returns:
            str: Porcentaje formateado
        """
        if number is None:
            return "0.00%"
        
        try:
            decimal_number = Decimal(str(number)) * 100
            format_string = f"{{:,.{decimal_places}f}}%"
            return format_string.format(float(decimal_number))
        except (ValueError, TypeError):
            return "0.00%"

class TextFormatter:
    """Formateador de texto"""
    
    @staticmethod
    def capitalize_words(text):
        """
        Capitalizar palabras
        
        Args:
            text (str): Texto a capitalizar
            
        Returns:
            str: Texto capitalizado
        """
        if not text:
            return ""
        return text.title()
    
    @staticmethod
    def clean_text(text):
        """
        Limpiar texto removiendo espacios extra
        
        Args:
            text (str): Texto a limpiar
            
        Returns:
            str: Texto limpio
        """
        if not text:
            return ""
        return " ".join(text.split())
    
    @staticmethod
    def truncate_text(text, max_length, suffix="..."):
        """
        Truncar texto si excede la longitud máxima
        
        Args:
            text (str): Texto a truncar
            max_length (int): Longitud máxima
            suffix (str): Sufijo para texto truncado
            
        Returns:
            str: Texto truncado
        """
        if not text or len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix

class InvoiceFormatter:
    """Formateador específico para facturas"""
    
    @staticmethod
    def format_invoice_number(number):
        """
        Formatear número de factura
        
        Args:
            number (int): Número de factura
            
        Returns:
            str: Número formateado (ej: FAC-000001)
        """
        if number is None:
            return ""
        
        try:
            return f"FAC-{int(number):06d}"
        except (ValueError, TypeError):
            return str(number)
    
    @staticmethod
    def format_invoice_state(state):
        """
        Formatear estado de factura para mostrar
        
        Args:
            state (str): Estado de factura
            
        Returns:
            str: Estado formateado
        """
        state_mapping = {
            'borrador': 'Borrador',
            'confirmada': 'Confirmada',
            'pagada': 'Pagada',
            'anulada': 'Anulada'
        }
        
        return state_mapping.get(state, state.capitalize() if state else "")

# Instancias globales para uso fácil
currency_formatter = CurrencyFormatter()
date_formatter = DateFormatter()
number_formatter = NumberFormatter()
text_formatter = TextFormatter()
invoice_formatter = InvoiceFormatter()