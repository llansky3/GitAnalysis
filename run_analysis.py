from GitAnalysis import GitAnalysis

if __name__ == '__main__':
    #package = 'cryptsetup'
    #package = 'jemalloc'
    #package = 'util-linux'
    #package = 'iptables'
    #package = 'kexec-tools'
    package = ''
    analysis = GitAnalysis(package)
    if not package:
        analysis.import_csv(f'output_{package}.csv')
    else:
        analysis.import_csv('output.csv')
    analysis.plot('lines_altered')