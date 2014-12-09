import unittest, time, sys, random, math, getpass
sys.path.extend(['.','..','../..','py'])
import h2o, h2o_cmd, h2o_import as h2i, h2o_util, h2o_print as h2p

def write_syn_dataset(csvPathname, rowCount, colCount, SEED, choices):
    r1 = random.Random(SEED)
    dsf = open(csvPathname, "w+")

    naCnt = [0 for j in range(colCount)]

    for i in range(rowCount):
        rowData = []
        for j in range(colCount):
            ri = random.choice(choices)
            if ri=='0' or ri==' 0':
                naCnt[j] += 1
            rowData.append(ri)
        rowDataCsv = ",".join(map(str,rowData))
        dsf.write(rowDataCsv + "\n")
    dsf.close()
    return naCnt

class Basic(unittest.TestCase):
    def tearDown(self):
        h2o.check_sandbox_for_errors()

    @classmethod
    def setUpClass(cls):
        global SEED
        SEED = h2o.setup_random_seed()
        h2o.init()

    @classmethod
    def tearDownClass(cls):
        h2o.tear_down_cloud()

    def test_summary2_NY0(self):
        SYNDATASETS_DIR = h2o.make_syn_dir()

        choicesList = [
            ('N', 'Y', '0'),
            ('n', 'y', '0'),
            ('F', 'T', '0'),
            ('f', 't', '0'),
            (' N', ' Y', ' 0'),
            (' n', ' y', ' 0'),
            (' F', ' T', ' 0'),
            (' f', ' t', ' 0'),
        ]

        # white space is stripped
        expectedList = [
            ('N', 'Y', '0'),
            ('n', 'y', '0'),
            ('F', 'T', '0'),
            ('f', 't', '0'),
            ('N', 'Y', '0'),
            ('n', 'y', '0'),
            ('F', 'T', '0'),
            ('f', 't', '0'),
        ]

        tryList = [
            # colname, (min, 25th, 50th, 75th, max)
            (100, 200, 'x.hex', choicesList[4], expectedList[4]),
            (100, 200, 'x.hex', choicesList[5], expectedList[5]),
            (100, 200, 'x.hex', choicesList[6], expectedList[6]),
            (100, 200, 'x.hex', choicesList[7], expectedList[7]),
            (100, 200, 'x.hex', choicesList[3], expectedList[3]),
            (1000, 200, 'x.hex', choicesList[2], expectedList[2]),
            (10000, 200, 'x.hex', choicesList[1], expectedList[1]),
            (100000, 200, 'x.hex', choicesList[0], expectedList[0]),
        ]

        timeoutSecs = 10
        trial = 1
        n = h2o.nodes[0]
        lenNodes = len(h2o.nodes)

        x = 0
        timeoutSecs = 60
        for (rowCount, colCount, hex_key, choices, expected) in tryList:
            # max error = half the bin size?
        
            SEEDPERFILE = random.randint(0, sys.maxint)
            x += 1

            csvFilename = 'syn_' + "binary" + "_" + str(rowCount) + 'x' + str(colCount) + '.csv'
            csvPathname = SYNDATASETS_DIR + '/' + csvFilename
            csvPathnameFull = h2i.find_folder_and_filename(None, csvPathname, returnFullPath=True)

            print "Creating random", csvPathname
            expectedNaCnt = write_syn_dataset(csvPathname, rowCount, colCount, SEEDPERFILE, choices)
            parseResult = h2i.import_parse(path=csvPathname, schema='put', hex_key=hex_key, timeoutSecs=10, doSummary=False)
            inspect = h2o_cmd.runInspect(key=hex_key)
            missingList, labelList, numRows, numCols = h2o_cmd.infoFromInspect(inspect)

            for i in range(colCount):
                # walks across the columns triggering a summary on the col desired
                summaryResult = h2o_cmd.runSummary(key=hex_key, column=i)
                # co is a returned object for the specified column. (is the summaryResult all columns?
                co = h2o_cmd.infoFromSummary(summaryResult, column=i)
                colname = co.label
                coltype = co.type
                nacnt = co.missing
                cardinality = co.domain
                hcntTotal = sum(co.bins)

                print "\nComparing column %s to expected" % i
                self.assertEqual(nacnt, expectedNaCnt[i], "Column %s Expected %s. nacnt %s incorrect" % (i, expectedNaCnt[i], nacnt))
                self.assertEqual(hcntTotal, rowCount - expectedNaCnt[i])
                self.assertEqual(rowCount, numRows, 
                    msg="numRows %s should be %s" % (numRows, rowCount))

            h2p.green_print("\nDone with trial", trial)
            trial += 1

            h2i.delete_keys_at_all_nodes()


if __name__ == '__main__':
    h2o.unit_main()

