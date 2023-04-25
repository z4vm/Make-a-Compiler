import copy # copiar Arbol
import re # manejo de expresiones regulares


def tokenizer(input_expression):
    current = 0
    tokens = []

    alphabet = re.compile(r"[a-z]",re.I)
    numbers = re.compile(r"[0-9]")
    white_spaces = re.compile(r"\s")

    while current < len(input_expression):
        char = input_expression[current]
        # Si nuestro caracter es un "space" lo ignoramos
        if re.match(white_spaces,char):
            # continua iterando
            current = current + 1
            continue
        # crea y añade un token para los parentesis de apertura
        if char == '(':
            tokens.append({
                'type': 'left_paren',
                'value': '('
            })
            current = current + 1
            continue
        # crea y añade un token para los parentesis de cierre
        if char == ')':
            tokens.append({
                'type': 'right_paren',
                'value': ')'
            })
            current = current + 1
            continue
        # crea y añade un token para los numeros
        if re.match(numbers, char):
            value = ''
            # itera para ver si el numero tiene mas digitos
            while re.match(numbers, char):
                value += char
                current = current+1
                char = input_expression[current];
            tokens.append({
                'type': 'number',
                'value': value
            })
            continue
        # crea y añade un token para las letras
        if re.match(alphabet, char):
            value = ''
            # itera para ver si las letras forman una palabra
            while re.match(alphabet, char):
                value += char
                current = current+1
                char = input_expression[current]
            tokens.append({
                'type': 'name',
                'value': value
            })
            continue
        # error si se ingreso un valor desconocido
        raise ValueError('what are THOSE?: ' + char);
    return tokens

def parser(tokens):
    global current
    current = 0
    def walk():
        global current
        token = tokens[current]
        # si se encuentra un número, devuelve un nodo "NumberLiteral"
        if token.get('type') == 'number':
            current = current + 1
            return {
                'type': 'NumberLiteral',
                'value': token.get('value')
            }
        # si se encuentran paréntesis abiertos, devuelve un nodo "CallExpression"
        if token.get('type') == 'left_paren':
            # saltarse el paréntesis, que no estamos almacenando
            current = current + 1 
            token = tokens[current]
            node = {
                'type': 'CallExpression',
                'name': token.get('value'),
                'params': []
            }
            # y este nodo tendrá nodos hijos como parámetros
            # Ademas la expresión de entrada puede tener muchas expresiones anidadas, así que usaremos la recursión para construir un árbol de relaciones.
            current = current + 1
            token = tokens[current]
            # hasta que la expresión termine con un paréntesis cerrado
            while token.get('type') != 'right_paren':
                # añadir recursivamente nodos al vector params mediante la función walk
                node['params'].append(walk());
                token = tokens[current]
            current = current + 1
            return node
        # error si se encuentra un tipo desconocido
        raise TypeError(token.get('type'))
    # Inicialicemos un Árbol de Sintaxis Abstracta vacío
    ast = {
        'type': 'Program',
        'body': []
    }
    # luego la rellenamos llamando a la función walk hasta que la variable global actual alcance el final de la matriz de tokens
    while current < len(tokens):
        ast['body'].append(walk())
    #retornamos el AST completo
    return ast    

# Función auxiliar para el transformador que permite recorrer nuestro AST recién creado        
def traverser(ast, visitor):
    # tomamos el nodo hijo (AST actual) y el nodo padre (nuevo AST) como entradas
    def traverseArray(array, parent):
    # iterar a través de cada elemento de parámetro en nuestro AST actual
        for child in array:
            # y atravesar cada
            traverseNode(child, parent)

    # volvemos a tomar el nodo hijo (AST actual) y el nodo padre (nuevo AST) como entradas.
    def traverseNode(node, parent):
        # esta es nuestra función transversal de más alto nivel almacena una referencia al nuevo AST
        method = visitor.get(node['type'])
        if method:
            method(node, parent)
        # si python tuviera un switch incorporado como JS, lol todo esta bien
        # podemos usar una serie de sentencias if si es el nivel superior
        if node['type'] == 'Program':
            # recorrer el cuerpo
            traverseArray(node['body'], node)
        # si es una call expression
        elif node['type'] == 'CallExpression':
            # recorrer parametros anidados
            traverseArray(node['params'], node)
        # si es un numero literal
        elif node['type'] == 'NumberLiteral':
          #break
            0
        else:
          #error por tipo desconocido 
            raise TypeError(node['type'])
        
    traverseNode(ast, None)

# utilizando nuestras funciones transversales recién creadas, transformaremos nuestro AST saliente en
def transformer(ast):
   # permite definir un nuevo AST vacío
    newAst = {
        'type': 'Program',
        'body': []
    }
    # copiaremos el antiguo y rellenaremos el nuevo con él
    oldAst = ast
    ast = copy.deepcopy(oldAst)
    # almacenemos una referencia al cuerpo de newAST en esta propiedad de contexto
    ast['_context'] = newAst.get('body')

    # función de ayuda cuando se encuentra una expresión de llamada 
    def CallExpressionTraverse(node, parent):
      # crear un nodo de expresión de llamada
        expression = {
            'type': 'CallExpression',
            'callee': {
                'type': 'Identifier',
                'name': node['name']
            },
            'arguments': []
        }
        # establece el contexto actual en su hijo args
        node['_context'] = expression['arguments']

        # almacenar referencias de expresiones de llamada anidadas
        if parent['type'] != 'CallExpression':
            expression = {
                'type': 'ExpressionStatement',
                'expression': expression
            }
        # almacenar la expresión en la propiedad context
        parent['_context'].append(expression)

    # Función de ayuda utilizada cuando se encuentra un número literal
    # durante el recorrido. Simplemente almacenaremos el nodo relevante cuando lo encontremos en la propiedad context
    def NumberLiteralTraverse(node, parent):
        parent['_context'].append({
            'type': 'NumberLiteral',
            'value': node['value']
        })
    # recorrer el AST utilizando nuestras funciones de ayuda hasta que hayamos rellenado completamente el nuevo AST
    traverser( ast , {
        'NumberLiteral': NumberLiteralTraverse,
        'CallExpression': CallExpressionTraverse 
    })
    #retornar el nuevo AST
    return newAst

# última parte Generación de código una función stringify recursiva que itera a través del AST 
# recién creado, nodo por nodo, continuamente construyendo 
# una cadena de salida dados los valores de cada nodo.
def codeGenerator(node):
    if node['type'] == 'Program':
        return '\n'.join([code for code in map(codeGenerator, node['body'])])
    elif node['type'] == 'Identifier':
        return node['name']
    elif node['type'] == 'NumberLiteral':
        return node['value']
    elif node['type'] == 'ExpressionStatement':
        expression = codeGenerator(node['expression']) 
        return '%s;' % expression
    elif node['type'] == 'CallExpression':
        callee = codeGenerator(node['callee']) 
        params = ', '.join([code for code in map(codeGenerator, node['arguments'])])
        return "%s(%s)" % (callee, params)
    else:
        raise TypeError(node['type'])

# Definimos la estructura de nuestro compilador
# traducir nuestro lenguaje a codigo C

def compiler(input_expression):
    tokens = tokenizer(input_expression)
    ast    = parser(tokens)
    newAst = transformer(ast)
    output = codeGenerator(newAst)
    return output

def main():
    #test 
    input = "(add 2 (subtract 4 2))"
    output = compiler(input)
    print(output)

if __name__ == "__main__":
    main()