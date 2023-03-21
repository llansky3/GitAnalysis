from GitAnalysis import GitAnalysis

if __name__ == '__main__':
    package = ''
    package = 'cryptsetup'
    package = 'jemalloc'
    #package = 'util-linux'
    package = 'iptables'
    #package = 'kexec-tools'
    analysis = GitAnalysis(package)
    if package:
        analysis.import_csv(f'output_{package}.csv')
    else:
        analysis.import_csv('output.csv')
    # analysis.plot('lines_altered')
    analysis.plot(90, 0.005, 'lines_weighted')