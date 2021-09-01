import unittest
import liskpool3


class TestGetVotesPercentages(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestGetVotesPercentages, self).__init__(*args, **kwargs)

    def test_blacklist(self):
        def mockedReq(conf, ep):
            return {
                "data": {
                    "votes": [
                        {"address": "A",
                         "amount": "10000000"},
                        {"address": "B",
                         "amount": "10000000"},
                    ]
                }
            }

        liskpool3.injectRequestHandler(mockedReq)

        conf = {
            "blackList": ["A"],
            "delegateName": "C",
            "includeSelfStake": False
        }
        res = liskpool3.getVotesPercentages(conf)
        self.assertEqual(
            res, [{'address': 'B', 'amount': '10000000', 'percentage': 100.0}])

    def test_blacklistEmpty(self):
        def mockedReq(conf, ep):
            return {
                "data": {
                    "votes": [
                        {"address": "A",
                         "amount": "10000000"},
                        {"address": "B",
                         "amount": "10000000"},
                    ]
                }
            }

        liskpool3.injectRequestHandler(mockedReq)

        conf = {
            "blackList": [],
            "delegateName": "C",
            "includeSelfStake": False
        }

        res = liskpool3.getVotesPercentages(conf)
        self.assertEqual(res, [{'address': 'A', 'amount': '10000000', 'percentage': 50.0}, {
                         'address': 'B', 'amount': '10000000', 'percentage': 50.0}])

    def test_includeSelfStakeFalse(self):
        def mockedReq(conf, ep):
            return {
                "data": {
                    "votes": [
                        {"address": "A", "username": "A",
                         "amount": "10000000"},
                        {"address": "B",
                         "amount": "10000000"},
                    ]
                }
            }

        liskpool3.injectRequestHandler(mockedReq)

        conf = {
            "blackList": [],
            "delegateName": "A",
            "includeSelfStake": True
        }

        res = liskpool3.getVotesPercentages(conf)
        self.assertEqual(res, [{'address': 'A', 'username': 'A', 'amount': '10000000', 'percentage': 50.0}, {'address': 'B', 'amount': '10000000', 'percentage': 50.0}])


    def test_includeSelfStakeFalse(self):
        def mockedReq(conf, ep):
            return {
                "data": {
                    "votes": [
                        {"address": "A", "username": "A",
                         "amount": "10000000"},
                        {"address": "B",
                         "amount": "10000000"},
                    ]
                }
            }

        liskpool3.injectRequestHandler(mockedReq)

        conf = {
            "blackList": [],
            "delegateName": "A",
            "includeSelfStake": False
        }

        res = liskpool3.getVotesPercentages(conf)
        self.assertEqual(res, [{'address': 'B', 'amount': '10000000', 'percentage': 100.0}])


if __name__ == '__main__':
    unittest.main()
