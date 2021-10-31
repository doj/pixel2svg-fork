all:
	@echo done

clean:
	$(RM) -r *~
	find . -type d -name __pycache__ | xargs $(RM) -r
