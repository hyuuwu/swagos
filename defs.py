
defaltcfgfl = "dontdeletethis.file"
def is_first_run():
    if not os.path.exists(defaltcfgfl):
        # This is the first run
        with open(defaltcfgfl, "w") as f:
            f.write(
                "hi,this is a file to check if the user ran this file. ever. if you want to delete it,its yo choice,but you gon redo the setup"
            )
        return True
    else:
        # Not the first run
        return False