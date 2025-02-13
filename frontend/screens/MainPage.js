import {useState,useEffect} from 'react';
import {StyleSheet,Text,View,TextInput,Image,Pressable,ScrollView,Keyboard} from 'react-native';
import { Checkbox } from 'expo-checkbox';
import {Dimensions} from 'react-native';
import {FontAwesome,MaterialIcons} from '@expo/vector-icons';
import useIsWeb from '../techniqueTools/useInWeb';
export const {width: screenWidth} = Dimensions.get("window");
export const {height: screenHeight} = Dimensions.get("window");
import {BookService,CombinedSearch,BookChoice,BookChoiceHighlight} from '../services/bookService';
import RenderHTML from 'react-native-render-html';
import Loader from './loader';
import { useFonts } from 'expo-font';


export default function MainPage(props){
    //const [suggests,setSuggest] = useState([]);
    const [authorCheckbox,setAuthorCheckbox] = useState(false);
    const [titleCheckbox,setTitleCheckbox] = useState(false);
    const [textCheckbox,setTextCheckbox] = useState(false);
    const [search,setSearch] = useState(false);
    const [booksInfos,setBooksInfos] = useState([]);
    const [suggestsInfos,setSuggestInfos] = useState([]);
    const [maxPagination,setMaxPagination] = useState(0);
    const [pagination,setPagination] = useState(1);
    const [popUpAdvancedSearch,setPopUpAdvancedSearch] = useState(false);
    const [text,setText] = useState("");
    const [where,setWhere] = useState("/author+title+text");
    const isWeb = useIsWeb();
    const [loadingProgress, setLoadingProgress] = useState(0);
    const [isLoading, setIsLoading] = useState(false);
    const [occurrenceIndicator, setOccurrenceIndicator] = useState(0);
    const [bookChoice, setBookChoice] = useState(0);
    const [bookId, setBookId] = useState(0);
    // const [fontsLoaded] = useFonts({
    //   'Arial': require('../assets/fonts/Arial.ttf'),
    // });
    let nbBook = isWeb ? 3 : 5;
    
    useEffect(() => {
      if(!bookChoice){
        if(!search){
          (async ()=>{
            response = await BookService(pagination,nbBook);
            setBooksInfos(response.books);
            setMaxPagination(Math.ceil(response.total_books/5))
            //console.log("test1",response.books)
          })()
        }else{
          (async ()=>{
            const response = await CombinedSearch(text,where,setLoadingProgress,pagination);
            //console.log("test2",response)
            setBooksInfos(response.books);
            setMaxPagination(Math.ceil(response.total_books/5))
          })()
        }
      }else{
        (async ()=>{
          console.log('entre 1!!!')
          if(search){
            response = await BookChoiceHighlight(bookId,pagination,text);
          }else{
            response = await BookChoice(bookId,pagination);
          }
          console.log('entre !!!',response)
          setBookChoice(response.text);
          setMaxPagination(Math.ceil(response.total_books))
        })()
      }
    },[pagination,search]);


    useEffect(() => {
      let where = "";
      authorCheckbox ? where = where+"author" : "";
      titleCheckbox ? where !== "" ? where = where+"+title" : where = where+"title" : "";
      textCheckbox  ? where !== "" ? where = where+"+text" : where = where+"text" : "";
      where === "" ? where = "/author+title+text" : where = "/"+where;
      setWhere(where);
    },[authorCheckbox,titleCheckbox,textCheckbox]);

    const handleSubmit = async () => {
      console.log('Validation par clavier ! Texte soumis :', text);
      setIsLoading(true);
      setLoadingProgress(0);
      try {
        const response = await CombinedSearch(text,where,setLoadingProgress,pagination);
        setBooksInfos(response.books);
        setSuggestInfos(response.suggestions);
        setMaxPagination(Math.ceil(response.total_books));
        setSearch(true);
        //console.log("test 3",response.total_occurrences);
        setOccurrenceIndicator(response.total_occurrences);
      } catch (error) {
        console.error("Erreur lors de la recherche:", error);
      } finally {
        setIsLoading(false);
        Keyboard.dismiss();
      }
      setPagination(1);
      setPopUpAdvancedSearch(false);
    };

    const suggestSubmit = async (choice) => {
      setText(choice);
      handleSubmit();
    }

    const bookSubmit = async (idBook) => {
        if(search){
          response = await BookChoiceHighlight(idBook,pagination,text);
        }else{
          response = await BookChoice(idBook,1);
        }
        setBookChoice(response.text);
        setMaxPagination(Math.ceil(response.total_books))
        setBookId(idBook);
        setPagination(1);
    }

    let books = [];
    let suggests = [<Pressable onPress={() => (setSearch(false),console.log("ouiiii"))} style={{borderWidth:0.5,borderRadius:7,padding:2,paddingHorizontal:4,marginLeft:"1%"}}><Text>X</Text></Pressable>];


    booksInfos.map((book,i)=>{
      books.push(
      <Pressable onPress={() => (bookSubmit(book.id),console.log("pressed"))}
      key={i} style={{width:"100%",height:isWeb ? screenHeight*0.19 : screenHeight*0.17,flexDirection:"row",backgroundColor:"white",alignItems:"center",paddingHorizontal:"2%"}}>
        <Image
          source={{uri: book.formats["image/jpeg"]}}
          style={{width:screenWidth*0.2,height:screenHeight*0.15}}
        ></Image>
        <View style={{height:"90%",margin:"2%",width:"75%"}}>
          <RenderHTML source={{ html: book.title }} tagsStyles={{body: {fontSize: 15,fontWeight: "400" }}} />
          <RenderHTML source={{ html: book.author.name }} tagsStyles={{body: {fontSize: 12,fontWeight: "350" }}} />
          <RenderHTML source={{ html: book.summary ? `${book.summary.substring(0, 200)}...` : "Résumé non disponible" }} tagsStyles={{body: {fontSize: 10,fontWeight: "300" }}}/>
        </View>
      </Pressable>)
    })

    if (Array.isArray(suggestsInfos)) {
      suggestsInfos.map((suggest,i)=>{
        suggests.unshift(
          <Pressable key={i} onPress={() => (suggestSubmit(suggest.word),console.log('send suggest'))}
          style={{borderWidth:0.5,borderRadius:7,padding:2,marginLeft:"1%"}}><Text>{suggest.word}</Text></Pressable>
        )
      })
    }

    return (
    <View style={styles.container}>
      <Loader visible={isLoading} progress={loadingProgress} />
      {/*header*/}
      <View style={{width:"100%",height:isWeb ? screenHeight*0.09 : screenHeight*0.115,flexDirection:"row",alignItems:"flex-end",justifyContent:"space-between",paddingTop:"0%",paddingHorizontal:"4%",paddingBottom:screenHeight*0.02,borderBottomWidth:0.5,borderColor:"black",backgroundColor:"white"}}>
        <Text style={{fontSize: screenHeight*0.03,fontWeight:"500"}}>Bibliothèque</Text>
        <View>
          <View style={{flexDirection:"row",justifyContent:"flex-end"}}>
              {bookChoice ? <></> : <>
              <TextInput
                  maxLength={30}
                  value={text}  // Assurez-vous de lier l'état ici
                  onChangeText={(text)=>setText(text)}
                  style={{width:screenWidth*0.54,height:screenHeight*0.040,borderWidth:0.5,maxWidth:"550px",borderRadius:10,fontSize:13}}
                  onSubmitEditing={handleSubmit}  // Ecoute l'appui sur la touche "Entrée"
              />
              {isWeb ? 
                <></>
                :  
              <View style={{borderWidth:0.5,position:"absolute",borderRadius:10,padding:"1%",paddingHorizontal:"1.5%",marginTop:"1%"}}>
                  <FontAwesome name="gear" size={screenHeight*0.029} color="black" onPress={()=>setPopUpAdvancedSearch(!popUpAdvancedSearch)}/>
              </View>} </>}
          </View>
          {/*Pop up recherche avancée*/}
          {popUpAdvancedSearch ?
          <View style={{borderWidth:0.5,borderColor:"black",width:"100%",flex:1,position:"absolute",marginTop:screenHeight*0.040,backgroundColor:"white",justifyContent:"center",paddingTop:"10%",paddingBottom:"25%",zIndex:2,borderRadius:5}}>
            <Text style={{fontSize:15,textDecorationLine:'underline',fontWeight: 'bold',alignSelf:"center"}}>Rechercher dans:</Text>
            <View style={styles.checkboxContainer}>
              <Checkbox value={authorCheckbox} onValueChange={setAuthorCheckbox} style={styles.checkbox}/>
              <Text style={styles.checkboxLLabel}>Auteur</Text>
            </View>
            <View style={styles.checkboxContainer}>
              <Checkbox value={titleCheckbox} onValueChange={setTitleCheckbox} style={styles.checkbox}/>
              <Text style={styles.checkboxLLabel}>Titre</Text>
            </View>
            <View style={styles.checkboxContainer}>
              <Checkbox value={textCheckbox} onValueChange={setTextCheckbox} style={styles.checkbox}/>
              <Text style={styles.checkboxLLabel}>Text</Text>
            </View>
          </View>
          : <></>}
        </View>
      </View>

      {/*Content*/}
      {suggests.length == 0 || bookChoice || !search ? <></> :
      <View style={{width:"100%",padding:"2%",flexDirection:"row"}}>
        <Text>Suggestion(s):</Text>
        {suggests}
      </View>}
      <ScrollView>
      {!bookChoice ? books : <RenderHTML source={{ html: `<pre>${bookChoice}</pre>` }} tagsStyles={{body: {fontSize: 15,fontWeight: "300",fontFamily: "Arial",padding:"5%"}}}/>}
      </ScrollView>
      
      {/*Footer*/}  
      {isWeb ? 
              <>
        <View style={{
          position: "absolute",
          marginTop: 73,
          right: 0,
          top: 0,
          width: "25%", 
          height: "100%",
          borderLeftWidth: 1,
          borderColor: "black",
          backgroundColor: "white",
          padding: 10
        }}>
        <Text style={{ fontSize: 16, fontWeight: "bold" }}>Recherche avancée dans:</Text>
        <View style={styles.checkboxContainer}>
          <Checkbox value={authorCheckbox} onValueChange={authorCheckbox} style={styles.checkbox}/>
          <Text style={styles.checkboxLLabel}>Auteur</Text>
        </View>
        <View style={styles.checkboxContainer}>
          <Checkbox value={titleCheckbox} onValueChange={setTitleCheckbox} style={styles.checkbox}/>
          <Text style={styles.checkboxLLabel}>Titre</Text>
        </View>
        <View style={styles.checkboxContainer}>
          <Checkbox value={textCheckbox} onValueChange={setTextCheckbox} style={styles.checkbox}/>
          <Text style={styles.checkboxLLabel}>Contenu</Text>
        </View>
        <Text style={{ marginTop: 20 }}>Aucune recherche lancée</Text>
        {/* Numérotation + Boutons */}
        <View style={{ flex: 1, justifyContent: "flex-end", alignItems: "center", paddingBottom: 75 }}>
          <Text>2/20</Text>
          <View style={{ flexDirection: "row", marginTop: 8 }}>
            <Pressable style={styles.navButton}>
              <MaterialIcons name="arrow-back-ios" size={25} color="black"/>
            </Pressable>
            <Pressable style={styles.navButton}>
              <MaterialIcons name="arrow-forward-ios" size={25} color="black"/>
            </Pressable>
          </View>
        </View>
      </View>

       </>
      :       
      <View style={{flexDirection:"row",justifyContent:"space-around",borderWidth:0.5,borderColor:"black",backgroundColor:"white",width:"100%",height:screenHeight*0.08,alignItems:"center", zIndex:2,paddingBottom:"3%"}}>
        <View>
          {search && !bookChoice ?
          <>
          <Text style={{fontSize:13,fontWeight: "500",marginHorizontal:"13%"}}>Résultats pour "{text}"</Text>
          <Text style={{fontSize:12,marginHorizontal:"13%"}}>{occurrenceIndicator} occurrence(s) trouvée(s)</Text>
          </>
          : bookChoice ? 
          <Pressable
          onPress={() => setBookChoice(0)}
          style={({ pressed }) => ({
            backgroundColor:"white",
            borderWidth: 0.5,
            padding: 10,
            borderRadius: 25,
            alignItems:"center"
          })}
          >
          <Text style={{fontSize:12,marginHorizontal:"13%"}}>Retour</Text>
          </Pressable>
          :
          <Text style={{fontSize:12,marginHorizontal:"13%"}}>Aucune recherche lancée</Text>
          }
        </View>
        <View style={{alignSelf:"flex-end",justifyContent:"flex-end"}}>
          <Text style={{fontSize:10,marginBottom:"10%"}}>{pagination}/{maxPagination}</Text>
        </View>
        <View style={{flexDirection:"row"}}>
          <Pressable
            onPress={() => pagination == 1 ? 0 : setPagination(pagination-1)}
            style={({ pressed }) => ({
              backgroundColor:"white",
              borderWidth: 0.5,
              padding: 5,
              borderRadius: 25,
              alignItems:"flex-end"
            })}
          >
            <MaterialIcons name="arrow-back-ios" size={screenWidth * 0.06} color="black" style={{padding:"1%", margin:"1%"}}/>
            </Pressable>
            <Pressable
              onPress={() => pagination == maxPagination ? 0 : (setPagination(pagination+1),console.log("+++"))}
              style={({ pressed }) => ({
                backgroundColor:"white",
                borderWidth: 0.5,
                padding: 5,
                borderRadius: 25,
                alignItems:"flex-end"
              })}
            >
              <MaterialIcons  name="arrow-forward-ios" size={screenWidth * 0.06} color="black" style={{padding:"1%", margin:"1%"}}/>
            </Pressable>

        </View>
      </View>}
    </View>
    );
}

const styles = StyleSheet.create({
  container:{
      flex:1,
      backgroundColor: 'white',
      alignItems: 'center',
      flexDirection:"column",
      justifyContent:"space-between",
      height:"100%",
      width:"100%"
  },
  card: {
      alignItems:'center',
      justifyContent:'center',
      backgroundColor:"#EAEAEA",
      borderRadius:4,
  },
  checkbox: {
    alignSelf: 'center',
    marginLeft: '5%',
  },
  checkboxContainer: {
    flexDirection:"row",
    marginVertical:"4%",
  },
  checkboxLLabel: {
    fontSize:15,
    marginLeft:"2%"
  }
});
