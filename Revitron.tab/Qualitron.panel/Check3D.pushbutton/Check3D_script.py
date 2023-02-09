from qualitron import View3DChecker


if __name__ == "__main__":
    try:
        View3DChecker.create()
    except:
        import traceback
        print(traceback.format_exc())

		

