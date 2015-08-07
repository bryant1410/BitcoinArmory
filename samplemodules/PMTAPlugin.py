# This is a sample plugin file that will be used to create a new tab
# in the Armory main window.  All plugin files (such as this one) will
# be injected with the globals() from ArmoryQt.py, which includes pretty
# much all of Bitcoin & Armory related stuff that you need.  So this
# file can use any utils or objects accessible to functions in ArmoryQt.py.
from PyQt4.Qt import QPushButton, QScrollArea, SIGNAL, QLabel, QLineEdit, \
   QTextEdit
from qtdefines import QRichLabel, makeVertFrame, makeHorizFrame, GETFONT, \
   relaxedSizeNChar, VERTICAL
from ui.WalletFrames import SelectWalletFrame
import re
from armoryengine.BDM import getBDM
from armoryengine.ArmoryOptions import getTestnetFlag

# Class name is required by the plugin framework.
class PluginObject(object):
   tabName = 'PMTA'
   maxVersion = '0.99'

   # NB: As a general rule of thumb, it's wise to not rely on access to anything
   # until the BDM is ready to go and/or Armory has finished loading itself. Any
   # code that must run before both conditions are satisfied (e.g., get info
   # from a wallet) may fail.
   def __init__(self, main):
      self.main = main
      self.wlt = None

      # Set up the GUI.
      headerLabel    = QRichLabel(tr("<b>PMTA-related Functions</b>"""),
                                  doWrap=False)
      addressLabel = QLabel('Choose wallet:')
      self.frmSelectedWlt = SelectWalletFrame(main, main, VERTICAL,
                                              selectWltCallback=self.setWallet)
      self.pksButton      = QPushButton('Save PKS Record')
      self.pmtaButton     = QPushButton('Save PMTA Record')
      self.payReqButton   = QPushButton('Payment Request')
      self.addIDButton    = QPushButton('Save Wallet ID')
      self.exportIDButton = QPushButton('Export Wallet ID')
      payReqLabel         = QLabel('Payment Request:')
      self.payReqTextArea = QTextEdit()
      self.payReqTextArea.setFont(GETFONT('Fixed', 8))
      w                   = relaxedSizeNChar(self.payReqTextArea, 68)[0]
      h                   = int(12 * 8.2)
      self.payReqTextArea.setMinimumWidth(w)
      self.payReqTextArea.setMinimumHeight(h)
      self.clearButton    = QPushButton('Clear')

      # Qt GUI calls must occur on the main thread. We need to update the frame
      # once the BDM is ready, so that the wallet balance is shown. To do this,
      # we register a signal with the main thread that can be used to call an
      # associated function.
      self.main.connect(self.main, SIGNAL('bdmReadyPMTA'), self.bdmReady)
      self.main.connect(self.main, SIGNAL('wltChangedPKS'), self.wltHasChanged)

      # Action for when the PKS button is pressed.
      def pksAction():
         self.savePKSFile()

      # Action for when the PMTA button is pressed.
      def pmtaAction():
         self.savePMTAFile()

      # Action for when the payment request button is pressed.
      def prAction():
         # TO BE COMPLETED
         # What we want to do is take the incoming PR Base58 string, decode it,
         # verify that it's valid, and open a pre-filled "Send Bitcoins" dialog.
         # Verfication includes checking DNS first and then checking the Armory
         # ID store (see the ID store plugin) if the record's not on DNS.

         # Decode the PR and confirm that it's valid.
         # NB: The text below is a Base58 form of PR1_v1. TEST PURPOSES ONLY!!!
         self.payReqTextArea.setText('h858t6j6fEGK7jMpGDV4mPQVAbX4xM4HnSRsYiXH5awbK2wYi3NXPEaLrqepQK3qmEm6sAepUaEiG5DZcfDLWuv1BstHsrjaAkdeYWY1tFkDhPknb6A3tgatSdm')
         prRawBin = base58_to_binary(str(self.payReqTextArea.toPlainText()))
         prFinal = PaymentRequest().unserialize(prRawBin)
         if prFinal.isValid() is False:
            QMessageBox.warning(self.main, 'Invalid Payment Request',
                                'Payment Request is invalid. Please confirm ' \
                                'that the text is complete and not corrupted.',
                                QMessageBox.Ok)
         else:
            # If the PR is valid, go through the following steps. All steps,
            # unless otherwise noted, are inside a loop based on the # of
            # unvalidated TxOut scripts listed in the record.
            #  1) Check DNS first.
            # 2a) If we get a DNS record, create TxOut using it & matching SRP.
            # 2b) If we don't get a DNS record, just use the unvalidated info.
            #     (In a prod env, the user would have an option. For now....)
            #  3) Generate a "Send Bitcoins" dialog using the appropriate info.

            # FOR NOW, DNS IS IGNORED. COME BACK LATER.

            # For now, this ONLY SUPPORTS ONE TxOut! Hacks may be required to
            # support multiple outputs. The nature of said hacks is TBD. Until
            # then, only the final TxOut will be seen.
            #
            # Also, there appears to be a bug in Armory SW. In dns-demo, you can
            # set the address in the "Send Bitcoins" dialog. Here, you can't.
            # The failure appears to originate in the SendBitcoinsFrame class.
            # makeRecipFrame() is apparently supposed to grab an address and
            # pass it along somehow. Instead, createAddressEntryWidgets
            # (ArmoryQt.py) has an empty initString var, which causes a failure.
            dlgInfo = {}
            for t in range(0, prFinal.numTxOutScripts):
               dlgInfo['address'] = \
                                script_to_addrStr(prFinal.unvalidatedScripts[t])
            DlgSendBitcoins(self.wlt, self.main, self.main, dlgInfo).exec_()

      # Action for when the add DNS wallet ID button is pressed.
      def addIDAction():
         # str() used so that we save the text to a file.
         wltDNSID = str(self.inID.displayText())

         # We'll allow a user to input a valid email address or enter no text at
         # all. To query DNS for a PMTA record, you must start with a string in
         # an external email address format, which is a tighter form of what's
         # allowed under RFC 822. We'll also let people enter blank text to
         # erase an address. This raises questions of how wallet IDs should be
         # handled in a production env. For now, the ID can change at will.
         if (wltDNSID != '') and (self.validateEmailAddress(wltDNSID) == False):
            QMessageBox.warning(self.main, 'Incorrect ID Formatting',
                                'ID is not blank or in the form of an email ' \
                                'address.',
                                QMessageBox.Ok)
         else:
            self.main.setWltSetting(self.wlt.uniqueIDB58, 'dnsID', wltDNSID)
            QMessageBox.information(self.main, 'ID Saved', 'ID is saved.',
                                    QMessageBox.Ok)

      # Action for when the export DNS wallet ID button is pressed.
      def exportIDAction():
         if (str(self.inID.displayText()) != '') and \
            (str(self.inID.displayText()) !=
             self.main.getWltSetting(self.wlt.uniqueIDB58, 'dnsID')):
            QMessageBox.warning(self.main, 'ID Not Saved',
                                'DNS wallet ID must be saved first.',
                                QMessageBox.Ok)
         elif str(self.main.getWltSetting(self.wlt.uniqueIDB58, 'dnsID')) == '':
            QMessageBox.warning(self.main, 'ID Not Saved',
                                'DNS wallet ID must be saved first.',
                                QMessageBox.Ok)
         else:
            # We need to preserve the email address-like string that is the
            # wallet ID. Two periods after the string is guaranteed to be
            # invalid for an email address, so we'll use that.
            expStr = self.main.getWltSetting(self.wlt.uniqueIDB58, 'dnsID') + \
                     '..' + self.pksB58Line.displayText()
            QMessageBox.information(self.main, 'Exportable DNS Wallet ID',
                                'The exportable DNS ID for wallet %s is %s' %
                                (self.wlt.uniqueIDB58, expStr),
                                QMessageBox.Ok)


      # Action for when the clear text button is pressed.
      def clearTextArea():
         self.payReqTextArea.setText('')

      self.main.connect(self.pksButton,      SIGNAL('clicked()'), pksAction)
      self.main.connect(self.pmtaButton,     SIGNAL('clicked()'), pmtaAction)
      self.main.connect(self.payReqButton,   SIGNAL('clicked()'), prAction)
      self.main.connect(self.addIDButton,    SIGNAL('clicked()'), addIDAction)
      self.main.connect(self.exportIDButton, SIGNAL('clicked()'), exportIDAction)
      self.main.connect(self.clearButton,    SIGNAL('clicked()'), clearTextArea)

      # ID stuff
      idLabel = QLabel('Public Wallet ID: ')
      self.inID = QLineEdit()
      self.inID.setFont(GETFONT('Fixed'))
      self.inID.setMinimumWidth(tightSizeNChar(GETFONT('Fixed'), 14)[0])
      self.inID.setAlignment(Qt.AlignLeft)
      idTip = self.main.createToolTipWidget('An ID, in email address form, ' \
                                            'that will be associated with ' \
                                            'this wallet in a DNS record.')

      # Base58 PKS stuff
      pksB58Label = QLabel('PKS (Base 58): ')
      self.pksB58Line = QLineEdit()
      self.pksB58Line.setFont(GETFONT('Fixed'))
      self.pksB58Line.setMinimumWidth(tightSizeNChar(GETFONT('Fixed'), 14)[0])
      self.pksB58Line.setAlignment(Qt.AlignLeft)
      self.pksB58Line.setReadOnly(True)
      pksB58Tip = self.main.createToolTipWidget('The wallet\'s PKS record, ' \
                                                'Base58-encoded.')

      # Create the frame and set the scrollarea widget to the layout.
      # self.tabToDisplay is required by the plugin framework.
      pluginFrame = makeVertFrame([headerLabel,
                                   makeHorizFrame([addressLabel,
                                                   'Stretch']),
                                   makeHorizFrame([self.frmSelectedWlt,
                                                   'Stretch']),
                                   makeHorizFrame([pksB58Label,
                                                   self.pksB58Line,
                                                   pksB58Tip,
                                                   'Stretch']),
                                   makeHorizFrame([idLabel,
                                                   self.inID,
                                                   idTip,
                                                   'Stretch']),
                                   makeHorizFrame([self.pksButton,
                                                   self.pmtaButton,
                                                   self.payReqButton,
                                                   self.addIDButton,
                                                   self.exportIDButton,
                                                   'Stretch']),
                                   payReqLabel,
                                   makeHorizFrame([self.payReqTextArea,
                                                   'Stretch']),
                                   makeHorizFrame([self.clearButton,
                                                   'Stretch']),
                                   'Stretch'])
      self.tabToDisplay = QScrollArea()
      self.tabToDisplay.setWidgetResizable(True)
      self.tabToDisplay.setWidget(pluginFrame)

      # Register the BDM callback for when the BDM sends signals.
      getBDM().registerCppNotification(self.handleBDMNotification)


   # Function that creates and returns a PublicKeySource (PMTA/DNS) record based
   # on the incoming wallet.
   # INPUT:  The wallet used to generate the PKS record (ABEK_StdWallet)
   #         PKS-related flags (bool) - See armoryengine/ConstructedScript.py
   # OUTPUT: None
   # RETURN: Final PKS record (PKSRecord)
   def getWltPKS(self, inWlt, isStatic = False, useCompr = False,
                 use160 = False, isUser = False, isExt = False,
                 chksumPres = False):
      # Start with the wallet's uncompressed root key.
      sbdPubKey33 = SecureBinaryData(inWlt.sbdPublicKey33)
      sbdPubKey65 = CryptoECDSA().UncompressPoint(sbdPubKey33)

      myPKS = PublicKeySource()
      myPKS.initialize(isStatic, useCompr, use160, isUser, isExt,
                       sbdPubKey65.toBinStr(), chksumPres)
      return myPKS


   # Call for when we want to save a binary PKS record to a file. By default,
   # all PKS flags will be false.
   # INPUT:  PKS-related flags (bool) - See armoryengine/ConstructedScript.py
   # OUTPUT: None
   # RETURN: Final PKS record (PKSRecord)
   def savePKSFile(self, isStatic = False, useCompr = False, use160 = False,
                   isUser = False, isExt = False, chksumPres = False):
      defName = 'armory_%s.pks' % self.wlt.uniqueIDB58
      filePath = unicode(self.main.getFileSave(defaultFilename = defName))
      myPKS = None

      if len(filePath) > 0:
         pathdir = os.path.dirname(filePath)
         if not os.path.exists(pathdir):
            raise FileExistsError('Path for new PMTA record does not ' \
                                  'exist: %s', pathdir)
         else:
            myPKS = getWltPKS(self.wlt, isStatic, useCompr, use160, isUser,
                              isExt, sbdPubKey65.toBinStr(), chksumPres)
            # Write the PKS record to the file, then return the record.
            try:
               with open(filePath, 'wb') as newWltFile:
                  newWltFile.write(binary_to_base58(myPKS.serialize()))
               QMessageBox.information(self.main, 'PKS File Saved',
                                       'PKS file is saved.', QMessageBox.Ok)
            except EnvironmentError:
               QMessageBox.warning(self.main, 'PKS File Save Failed',
                                   'PKS file save failed. Please check your ' \
                                   'file system.', QMessageBox.Ok)
               myPKS = None

      return myPKS


   # Call for when we want to save a binary PMTA record to a file. The PMTA
   # record will include a PKS record for the currently selected wallet. By
   # default, all PKS flags will be false, except for the flag adding a checksum
   # to the PKS record.
   # INPUT:  PKS-related flags (bool) - See armoryengine/ConstructedScript.py
   # OUTPUT: None
   # RETURN: Final PMTA record (PMTARecord)
   def savePMTAFile(self, isStatic = False, useCompr = False, use160 = False,
                    isUser = False, isExt = False, chksumPres = True):
      myPMTA = None

      defName = 'armory_%s.pmta' % self.wlt.uniqueIDB58
      payNet = PAYNET_BTC
      if getTestnetFlag():
         payNet = PAYNET_TBTC

      filePath = unicode(self.main.getFileSave(defaultFilename = defName))
      if not len(filePath) > 0:
         return myPMTA
      else:
         # Start with the wallet's uncompressed root key.
         sbdPubKey33 = SecureBinaryData(self.wlt.sbdPublicKey33)
         sbdPubKey65 = CryptoECDSA().UncompressPoint(sbdPubKey33)

         pathdir = os.path.dirname(filePath)
         if not os.path.exists(pathdir):
            raise FileExistsError('Path for new PKS record does not ' \
                                  'exist: %s', pathdir)

         # Write the PMTA record to the file, then return the record.
         myPMTA = PMTARecord()
         try:
            with open(filePath, 'wb') as newWltFile:
               myPKS = PublicKeySource()
               myPKS.initialize(isStatic, useCompr, use160, isUser, isExt,
                                sbdPubKey65.toBinStr(), chksumPres)
               myPMTA.initialize(myPKS.serialize(), payNet)
               newWltFile.write(binary_to_base58(myPMTA.serialize()))
               QMessageBox.information(self.main, 'PMTA File Saved',
                                       'PMTA file is saved.', QMessageBox.Ok)
         except EnvironmentError:
            QMessageBox.warning(self.main, 'PKS File Save Failed',
                                'PKS file save failed. Please check your ' \
                                'file system.', QMessageBox.Ok)
            myPMTA = None

      return myPMTA


   # Validate an email address. Necessary to ensure that the DNS wallet ID is
   # valid. http://www.ex-parrot.com/pdw/Mail-RFC822-Address.html is the source
   # of the (ridiculously long) regex expression. It does not appear to have any
   # licensing restrictions. Using Python's bult-in email.utils.parseaddr would
   # be much cleaner. Unfortunately, it permits a lot of strings that are valid
   # under RFC 822 but are not valid email addresses. It may be worthwhile to
   # add validate_email (https://github.com/syrusakbary/validate_email) to the
   # Armory source tree eventually and just remove this regex abomination.
   # INPUT:  A string with an email address to validate.
   # OUTPUT: None
   # RETURN: A boolean indicating if the email address is valid.
   def validateEmailAddress(self, inAddr):
      validAddr = True
      if not re.match(r'(?:(?:\r\n)?[ \t])*(?:(?:(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|"(?:[^\"\r\\]|\\.|(?:(?:\r\n)?[ \t]))*"(?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|"(?:[^\"\r\\]|\\.|(?:(?:\r\n)?[ \t]))*"(?:(?:\r\n)?[ \t])*))*@(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*))*|(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|"(?:[^\"\r\\]|\\.|(?:(?:\r\n)?[ \t]))*"(?:(?:\r\n)?[ \t])*)*\<(?:(?:\r\n)?[ \t])*(?:@(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*))*(?:,@(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*))*)*:(?:(?:\r\n)?[ \t])*)?(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|"(?:[^\"\r\\]|\\.|(?:(?:\r\n)?[ \t]))*"(?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|"(?:[^\"\r\\]|\\.|(?:(?:\r\n)?[ \t]))*"(?:(?:\r\n)?[ \t])*))*@(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*))*\>(?:(?:\r\n)?[ \t])*)|(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|"(?:[^\"\r\\]|\\.|(?:(?:\r\n)?[ \t]))*"(?:(?:\r\n)?[ \t])*)*:(?:(?:\r\n)?[ \t])*(?:(?:(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|"(?:[^\"\r\\]|\\.|(?:(?:\r\n)?[ \t]))*"(?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|"(?:[^\"\r\\]|\\.|(?:(?:\r\n)?[ \t]))*"(?:(?:\r\n)?[ \t])*))*@(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*))*|(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|"(?:[^\"\r\\]|\\.|(?:(?:\r\n)?[ \t]))*"(?:(?:\r\n)?[ \t])*)*\<(?:(?:\r\n)?[ \t])*(?:@(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*))*(?:,@(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*))*)*:(?:(?:\r\n)?[ \t])*)?(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|"(?:[^\"\r\\]|\\.|(?:(?:\r\n)?[ \t]))*"(?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|"(?:[^\"\r\\]|\\.|(?:(?:\r\n)?[ \t]))*"(?:(?:\r\n)?[ \t])*))*@(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*))*\>(?:(?:\r\n)?[ \t])*)(?:,\s*(?:(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|"(?:[^\"\r\\]|\\.|(?:(?:\r\n)?[ \t]))*"(?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|"(?:[^\"\r\\]|\\.|(?:(?:\r\n)?[ \t]))*"(?:(?:\r\n)?[ \t])*))*@(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*))*|(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|"(?:[^\"\r\\]|\\.|(?:(?:\r\n)?[ \t]))*"(?:(?:\r\n)?[ \t])*)*\<(?:(?:\r\n)?[ \t])*(?:@(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*))*(?:,@(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*))*)*:(?:(?:\r\n)?[ \t])*)?(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|"(?:[^\"\r\\]|\\.|(?:(?:\r\n)?[ \t]))*"(?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|"(?:[^\"\r\\]|\\.|(?:(?:\r\n)?[ \t]))*"(?:(?:\r\n)?[ \t])*))*@(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*))*\>(?:(?:\r\n)?[ \t])*))*)?;\s*)', inAddr):
         validAddr = False

      return validAddr


   # Callback function for when the user selects a wallet. Be careful, as some
   # objects (GUI objects, most likely) aren't acceptable, probably due to the
   # function being called before Armory is ready to be displayed.
   def setWallet(self, wlt):
      self.wlt = wlt

      # Signal doesn't work when first called. Probably due to Armory not being
      # fully loaded just yet. This is acceptable.
      self.main.emit(SIGNAL('wltChangedPKS'))


   # Function called when the "bdmReadyPMTA" signal is emitted. Updates the
   # wallet balance on startup.
   def bdmReady(self):
      # Update wallet balance
      self.frmSelectedWlt.updateOnWalletChange()

      # Get the PKS record and display it as a Base58-encoded string. Used only
      # for the initial string load.
      if self.wlt is not None:
         wltPKS = binary_to_base58(self.getWltPKS(self.wlt).serialize())
         self.pksB58Line.setText(wltPKS)

         # If it exists, get the DNS wallet ID.
         wltDNSID = self.main.getWltSetting(self.wlt.uniqueIDB58, 'dnsID')
         self.inID.setText(wltDNSID)


   # Function called when the "wltChangedPKS" signal is emitted. Updates the
   # QLineEdit object showing the wallet's Base58-encoded PKS record.
   def wltHasChanged(self):
      if self.wlt is None:
         self.pksB58Line.setText('')
      else:
         wltPKS = binary_to_base58(self.getWltPKS(self.wlt).serialize())
         self.pksB58Line.setText(wltPKS)

         # If it exists, get the DNS wallet ID.
         wltDNSID = self.main.getWltSetting(self.wlt.uniqueIDB58, 'dnsID')
         self.inID.setText(wltDNSID)


   # Place any code here that must be executed when the BDM emits a signal. The
   # only thing we do is emit a signal so that the call updating the GUI can be
   # called by the main thread. (Qt GUI requirement, lest Armory crash due to a
   # non-main thread updating the GUI. This updates wallet-related info.
   def handleBDMNotification(self, action, args):
      if action == FINISH_LOAD_BLOCKCHAIN_ACTION:
         self.main.emit(SIGNAL('bdmReadyPMTA'))


   # Function is required by the plugin framework.
   def getTabToDisplay(self):
      return self.tabToDisplay
