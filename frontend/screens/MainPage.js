import {useState} from 'react';
import {StyleSheet,Text,View,TextInput,Image,Pressable} from 'react-native';
import { Checkbox } from 'expo-checkbox';
import {Dimensions} from 'react-native';
import {FontAwesome,MaterialIcons} from '@expo/vector-icons';
import useIsWeb from '../techniqueTools/useInWeb';
export const {width: screenWidth} = Dimensions.get("window");
export const {height: screenHeight} = Dimensions.get("window");


export default function MainPage(props){
    //const [suggests,setSuggest] = useState([]);
    const [filterCheckbox,setFilterCheckbox] = useState(false);
    const [titleCheckbox,setTitleCheckbox] = useState(false);
    const [textCheckbox,setTextCheckbox] = useState(false);
    const [emailPretension,setEmailPretension] = useState("");
    const [popUpAdvancedSearch,setPopUpAdvancedSearch] = useState(false);
    const isWeb = useIsWeb();

    let books = [];
    let suggests = [];

    for(let i=0;i<4;i++){
      books.push(
      <Pressable key={i} style={{width:"100%",height:isWeb ? screenHeight*0.19 : screenHeight*0.17,flexDirection:"row",backgroundColor:"white",alignItems:"center",paddingHorizontal:"2%"}}>
        <Image
          source={require("../assets/pg791.cover.medium.jpg")}
          style={{width:screenWidth*0.2,height:screenHeight*0.15}}
        ></Image>
        <View style={{height:"90%",margin:"2%",width:"75%"}}>
          <Text style={{fontSize: 20,fontWeight:"500"}}>Titre</Text>
          <Text style={{fontSize: 10,fontWeight:"300"}}>Auteur (date - date)</Text>
          <Text style={{fontSize: 10,fontWeight:"300"}}>Préambule - Eo adducta re per Isauriam, rege 
            Persarum bellis finitimis inligato repellenteque
            a conlimitiis suis ferocissimas gentes, quae 
            mente quadam versabili hostiliter eum saep...</Text>
        </View>
      </Pressable>)
    }

    for(let i=0;i<3;i++){
      suggests.push(
        <Pressable key={i} style={{borderWidth:0.5,borderRadius:7,padding:2,marginLeft:"1%"}}><Text>Antoinettes</Text></Pressable>
      )
    }

    return (
    <View style={styles.container}>
      {/*header*/}
      <View style={{width:"100%",height:isWeb ? screenHeight*0.09 : screenHeight*0.115,flexDirection:"row",alignItems:"flex-end",justifyContent:"space-between",paddingTop:"0%",paddingHorizontal:"4%",paddingBottom:screenHeight*0.02,borderBottomWidth:0.5,borderColor:"black",backgroundColor:"white"/*,elevation:5*/}}>
        <Text style={{fontSize: screenHeight*0.03,fontWeight:"500"}}>Bibliothèque</Text>
        <View>
          <View style={{flexDirection:"row",justifyContent:"flex-end"}}>
              <TextInput
                  maxLength={30}
                  onChangeText={(text)=>setEmailPretension(text)}
                  style={{width:screenWidth*0.54,height:screenHeight*0.040,borderWidth:0.5,maxWidth:"550px",borderRadius:10,fontSize:13}}
              />
              {isWeb ? 
                <></>
                :  
              <View style={{borderWidth:0.5,position:"absolute",borderRadius:10,padding:"1%",paddingHorizontal:"1.5%",marginTop:"1%"}}>
                  <FontAwesome name="gear" size={screenHeight*0.029} color="black" onPress={()=>setPopUpAdvancedSearch(!popUpAdvancedSearch)}/>
              </View>}
          </View>
          {/*Pop up recherche avancée*/}
          {popUpAdvancedSearch ?
          <View style={{borderWidth:0.5,borderColor:"black",width:"100%",flex:1,position:"absolute",marginTop:screenHeight*0.040,backgroundColor:"white",justifyContent:"center",paddingTop:"10%",paddingBottom:"25%",zIndex:2}}>
            <Text style={{fontSize:15,textDecorationLine:'underline',fontWeight: 'bold',alignSelf:"center"}}>Rechercher dans:</Text>
            <View style={styles.checkboxContainer}>
              <Checkbox value={filterCheckbox} onValueChange={setFilterCheckbox} style={styles.checkbox}/>
              <Text style={styles.checkboxLLabel}>Filtrer</Text>
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
      {suggests.length == 0 ? <></> :
      <View style={{width:"100%",padding:"2%",flexDirection:"row"}}>
        <Text>Suggestion(s):</Text>
        {suggests}
      </View>}
      
      {books}

      {/*Footer*/}  
      {isWeb ? 
        <></>
      :       
      <View style={{flexDirection:"row",justifyContent:"space-around",borderWidth:0.5,borderColor:"black",backgroundColor:"white",width:"100%",height:screenHeight*0.08,alignItems:"center", zIndex:2,paddingBottom:"3%"}}>
        <View>
          <Text style={{fontSize:12,marginHorizontal:"13%"}}>Aucune recherche lance</Text>
        </View>
        <View style={{alignSelf:"flex-end",justifyContent:"flex-end"}}>
          <Text style={{fontSize:10,marginBottom:"10%"}}>1/270</Text>
        </View>
        <View style={{flexDirection:"row"}}>
          <Pressable
            onPress={() => console.log("Pressé !")}
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
              onPress={() => console.log("Pressé !")}
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
