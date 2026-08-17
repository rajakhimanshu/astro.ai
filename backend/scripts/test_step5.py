try:
    from core.agent import _build_context
except ImportError:
    from backend.core.agent import _build_context

try:
    question = "What does my chart say about career success and growth?"
    print(f"TESTING CONTEXT BUILDING FOR QUESTION: {question}")
    
    context = _build_context(question)
    print("\n" + "="*50)
    print("BUILT CONTEXT:")
    print("="*50)
    print(context)
    
except Exception as e:
    import traceback
    traceback.print_exc()
