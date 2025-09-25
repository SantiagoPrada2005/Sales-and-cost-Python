#!/usr/bin/env python3
"""
Pruebas simplificadas para el modelo base
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_base_model_import():
    """Probar que el BaseModel se puede importar correctamente"""
    print("\n🔍 Probando importación del BaseModel...")
    
    try:
        from models.base_model import BaseModel
        print("✅ BaseModel importado correctamente")
        return True
    except Exception as e:
        print(f"❌ Error importando BaseModel: {e}")
        return False

def test_base_model_abstract():
    """Probar que BaseModel es abstracto"""
    print("\n🔍 Probando que BaseModel es abstracto...")
    
    try:
        from models.base_model import BaseModel
        
        # Intentar crear instancia directa (debería fallar)
        try:
            BaseModel()
            print("❌ BaseModel debería ser abstracto")
            return False
        except TypeError as e:
            if "abstract" in str(e).lower():
                print("✅ BaseModel es correctamente abstracto")
                return True
            else:
                print(f"❌ Error inesperado: {e}")
                return False
    except Exception as e:
        print(f"❌ Error en prueba de abstracción: {e}")
        return False

def test_base_model_inheritance():
    """Probar que se puede heredar de BaseModel"""
    print("\n🔍 Probando herencia de BaseModel...")
    
    try:
        from models.base_model import BaseModel
        
        class TestModel(BaseModel):
            def get_table_name(self):
                return "test_table"
        
        # Crear instancia de la clase hija
        model = TestModel()
        print("✅ Se puede heredar de BaseModel")
        
        # Verificar que tiene métodos esperados
        expected_methods = ['find_by_id', 'find_all', 'delete_by_id', 'insert', 'update']
        
        for method in expected_methods:
            if hasattr(model, method):
                print(f"✅ Método {method} existe")
            else:
                print(f"❌ Método {method} no existe")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba de herencia: {e}")
        return False

def test_base_model_table_name():
    """Probar que get_table_name funciona"""
    print("\n🔍 Probando método get_table_name...")
    
    try:
        from models.base_model import BaseModel
        
        class TestModel(BaseModel):
            def get_table_name(self):
                return "test_table"
        
        model = TestModel()
        table_name = model.get_table_name()
        
        if table_name == "test_table":
            print("✅ get_table_name funciona correctamente")
            return True
        else:
            print(f"❌ get_table_name devolvió: {table_name}")
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba de get_table_name: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 PRUEBAS SIMPLIFICADAS DEL MODELO BASE")
    print("=" * 60)
    
    success = True
    
    if not test_base_model_import():
        success = False
    
    if not test_base_model_abstract():
        success = False
    
    if not test_base_model_inheritance():
        success = False
    
    if not test_base_model_table_name():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 TODAS LAS PRUEBAS DEL MODELO BASE PASARON")
    else:
        print("💥 ALGUNAS PRUEBAS DEL MODELO BASE FALLARON")
    print("=" * 60)
    
    sys.exit(0 if success else 1)