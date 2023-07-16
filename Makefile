ALL:
	dita -i ../contrib/dita-ot-docs/userguide.ditamap -o /tmp/creating-plugins -f dita
	python -m automarkup_training_toolkit ../contrib/dita-ot-docs/topics --output_dir out
	python -m automarkup_training_toolkit ../contrib/dita-ot-docs/samples --output_dir out --doctype Task
